from django.conf.urls.defaults import patterns
from satchmo_store.shop.satchmo_settings import get_satchmo_setting

ssl = get_satchmo_setting('SSL', default_value=False)

urlpatterns = patterns('',
     (r'^$', 'satchmo_pagseguro.pagseguro.views.pay_ship_info', {'SSL': ssl}, 'PAGSEGURO_satchmo_checkout-step2'),
     (r'^confirm/$', 'satchmo_pagseguro.pagseguro.views.confirm_info', {'SSL': ssl}, 'PAGSEGURO_satchmo_checkout-step3'),
     (r'^success/$', 'payment.views.checkout.success', {'SSL': ssl}, 'PAGSEGURO_satchmo_checkout-success'),
     (r'^ipn/$', 'satchmo_pagseguro.pagseguro.views.ipn', {'SSL': ssl}, 'PAGSEGURO_satchmo_checkout-ipn'),
     (r'^confirmorder/$', 'payment.views.confirm.confirm_free_order',
         {'SSL' : ssl, 'key' : 'PAYPAL'}, 'PAGSEGURO_satchmo_checkout_free-confirm')
)
