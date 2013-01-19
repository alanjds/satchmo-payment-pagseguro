from decimal import Decimal
from django.conf import settings
from django.core import urlresolvers
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.http import urlencode
from django.utils.translation import ugettext as _
from django.views.decorators.cache import never_cache
from livesettings import config_get_group, config_value
from payment.config import gateway_live
from payment.utils import get_processor_by_key
from payment.views import payship
from satchmo_store.shop.models import Cart
from satchmo_store.shop.models import Order, OrderPayment
from satchmo_store.contact.models import Contact
from satchmo_utils.dynamic import lookup_url, lookup_template
from sys import exc_info
from traceback import format_exception
import logging
import urllib2
from django.views.decorators.csrf import csrf_exempt

from pagseguropy.pagseguro import Pagseguro

log = logging.getLogger()

def pay_ship_info(request):
    return payship.base_pay_ship_info(request,
        config_get_group('PAYMENT_PAGSEGURO'), payship.simple_pay_ship_process_form,
        'shop/checkout/pagseguro/pay_ship.html')
pay_ship_info = never_cache(pay_ship_info)


def confirm_info(request):
    payment_module = config_get_group('PAYMENT_PAGSEGURO')

    try:
        order = Order.objects.from_request(request)
    except Order.DoesNotExist:
        url = lookup_url(payment_module, 'satchmo_checkout-step1')
        return HttpResponseRedirect(url)

    tempCart = Cart.objects.from_request(request)
    if tempCart.numItems == 0 and not order.is_partially_paid:
        template = lookup_template(payment_module, 'shop/checkout/empty_cart.html')
        return render_to_response(template,
                                  context_instance=RequestContext(request))

    # Check if the order is still valid
    if not order.validate(request):
        context = RequestContext(request,
                                 {'message': _('Your order is no longer valid.')})
        return render_to_response('shop/404.html', context_instance=context)

    template = lookup_template(payment_module, 'shop/checkout/pagseguro/confirm.html')
    if payment_module.LIVE.value:
        log.debug("live order on %s", payment_module.KEY.value)
        url = payment_module.POST_URL.value
        account = payment_module.BUSINESS.value
    else:
        url = payment_module.POST_TEST_URL.value
        account = payment_module.BUSINESS_TEST.value

    try:
        address = lookup_url(payment_module,
            payment_module.RETURN_ADDRESS.value, include_server=True)
    except urlresolvers.NoReverseMatch:
        address = payment_module.RETURN_ADDRESS.value

    try:
        cart = Cart.objects.from_request(request)
    except:
        cart = None
    try:
        contact = Contact.objects.from_request(request)
    except:
        contact = None
    if cart and contact:
        cart.customer = contact
        log.debug(':::Updating Cart %s for %s' % (cart, contact))
        cart.save()

    processor_module = payment_module.MODULE.load_module('processor')
    processor = processor_module.PaymentProcessor(payment_module)
    processor.create_pending_payment(order=order)
    default_view_tax = config_value('TAX', 'DEFAULT_VIEW_TAX')

    order.add_status("Temp")

    recurring = None

    pagseguro = Pagseguro(tipo='CP', email_cobranca=account, moeda='BRL', encoding='UTF-8', ref_transacao=order.id, tipo_frete='EN')
    pagseguro.cliente(nome=order.contact.first_name,
                        end=order.contact.billing_address.street1,
                        cep=order.contact.billing_address.postal_code,
                        email=order.contact.email,
                     )

    for item in order.orderitem_set.all():
        pagseguro.item(id=item.product.id, 
                        descr=item.description, 
                        qty=int(item.quantity), 
                        valor="%.2f" % item.unit_price, 
                        peso=int(item.product.weight or 0)
                      )

    pagsegurohtml = pagseguro.mostra(imprime=False, abre=False, fecha=False)

    # Run only if subscription products are installed
    if 'product.modules.subscription' in settings.INSTALLED_APPS:
        order_items = order.orderitem_set.all()
        for item in order_items:
            if not item.product.is_subscription:
                continue

            recurring = {'product':item.product, 'price':item.product.price_set.all()[0].price.quantize(Decimal('.01')),}
            trial0 = recurring['product'].subscriptionproduct.get_trial_terms(0)
            if len(order_items) > 1 or trial0 is not None or recurring['price'] < order.balance:
                recurring['trial1'] = {'price': order.balance,}
                if trial0 is not None:
                    recurring['trial1']['expire_length'] = trial0.expire_length
                    recurring['trial1']['expire_unit'] = trial0.subscription.expire_unit[0]
                # else:
                #     recurring['trial1']['expire_length'] = recurring['product'].subscriptionproduct.get_trial_terms(0).expire_length
                trial1 = recurring['product'].subscriptionproduct.get_trial_terms(1)
                if trial1 is not None:
                    recurring['trial2']['expire_length'] = trial1.expire_length
                    recurring['trial2']['expire_unit'] = trial1.subscription.expire_unit[0]
                    recurring['trial2']['price'] = trial1.price

    ctx = RequestContext(request, {'order': order,
     'post_url': url,
     'default_view_tax': default_view_tax,
     'business': account,
     'currency_code': payment_module.CURRENCY_CODE.value,
     'return_address': address,
     'invoice': order.id,
     'pagseguro': pagsegurohtml,
     'subscription': recurring,
     'PAYMENT_LIVE' : gateway_live(payment_module)
    })

    return render_to_response(template, context_instance=ctx)
confirm_info = never_cache(confirm_info)

@csrf_exempt
def ipn(request):
    """
    PagSeguro IPN (Instant Payment Notification)
    Cornfirms that payment has been completed and marks invoice as paid.
    """
    payment_module = config_get_group('PAYMENT_PAGSEGURO')
    if payment_module.LIVE.value:
        log.debug("Live IPN on %s", payment_module.KEY.value)
        url = payment_module.IPN_URL.value
        account = payment_module.BUSINESS.value
    else:
        log.debug("Test IPN on %s", payment_module.KEY.value)
        url = payment_module.IPN_TEST_URL.value
        account = payment_module.BUSINESS_TEST.value
    PP_URL = url

    try:
        data = request.POST
        log.debug("PagSeguro IPN data: " + repr(data))
        if not confirm_ipn_data(data, PP_URL, payment_module.TOKEN.value):
            return HttpResponseRedirect(urlresolvers.reverse('satchmo_checkout-success'))
            #return HttpResponse()

        if not 'StatusTransacao' in data or not data['StatusTransacao'] in ("Completo","Aprovado"):
            # We want to respond to anything that isn't a payment - but we won't insert into our database.
             log.info("Ignoring IPN data for non-completed payment.")
             return HttpResponse()

        try:
            invoice = int(data['Referencia'])
        except:
            invoice = -1
        txn_id = data['TransacaoID']

        if not OrderPayment.objects.filter(transaction_id=txn_id).count():
            # If the payment hasn't already been processed:
            order = Order.objects.get(pk=invoice)

            # If we are testing set a shipping cost of 5,00
            if not payment_module.LIVE.value:
                order.shipping_cost = Decimal('5.0')
            else:
                order.shipping_cost = Decimal(data['ValorFrete'].replace(",", "."))
            order.recalculate_total(save=True) #order.save()

            try:
                order.ship_addressee = data['CliNome']
                order.ship_street1 = data['CliEndereco']
                order.ship_city = data['CliCidade']
                order.ship_state = data['CliEstado']
                order.ship_postal_code = data['CliCEP']
                order.save()
            except Exception, e:
                log.warn("Error setting ship info: %s", str(e))

            order.add_status(status='New', notes="Pago via PagSeguro")
            processor = get_processor_by_key('PAYMENT_PAGSEGURO')
            payment = processor.record_payment(order=order, amount=order.total, transaction_id=txn_id)

            if 'Anotacao' in data:
                if order.notes:
                    notes = order.notes + "\n"
                else:
                    notes = ""

                order.notes = notes + _('---Comment via PagSeguro IPN---') + u'\n' + data['Anotacao']
                order.save()
                log.debug("Saved order notes from PagSeguro")

            # Run only if subscription products are installed
            if 'product.modules.subscription' in settings.INSTALLED_APPS:
                for item in order.orderitem_set.filter(product__subscriptionproduct__recurring=True, completed=False):
                    item.completed = True
                    item.save()

            for cart in Cart.objects.filter(customer=order.contact):
                cart.empty()

    except:
        log.exception(''.join(format_exception(*exc_info())))

    return HttpResponse()

def confirm_ipn_data(data, PP_URL, token):
    # data is the form data that was submitted to the IPN URL.

    if not data:
        return False

    newparams = {}
    for key in data.keys():
        newparams[key] = data[key]

    newparams['Comando'] = "validar"
    newparams['Token'] = token
    params = urlencode(newparams)

    req = urllib2.Request(PP_URL)
    req.add_header("Content-type", "application/x-www-form-urlencoded")
    fo = urllib2.urlopen(req, params)

    ret = fo.read()
    if ret.lower() == "verificado":
        log.info("PayPal IPN data verification was successful.")
    else:
        log.info("PayPal IPN data verification failed.")
        log.debug("HTTP code %s, response text: '%s'" % (fo.code, ret))
        return False

    return True
