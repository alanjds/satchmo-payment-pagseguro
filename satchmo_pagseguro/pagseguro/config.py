from livesettings import *
from django.utils.translation import ugettext_lazy as _

PAYMENT_GROUP = ConfigurationGroup('PAYMENT_PAGSEGURO',
    _('PagSeguro Payment Module Settings'),
    ordering = 101)

config_register_list(

StringValue(PAYMENT_GROUP,
    'CURRENCY_CODE',
    description=_('Currency Code'),
    help_text=_('Currency code for PagSeguro transactions.'),
    default = 'BRL'),

StringValue(PAYMENT_GROUP,
    'POST_URL',
    description=_('Post URL'),
    help_text=_('The PagSeguro URL for real transaction posting.'),
    default="https://pagseguro.uol.com.br/security/webpagamentos/webpagto.aspx"),

StringValue(PAYMENT_GROUP,
    'POST_TEST_URL',
    description=_('Post URL'),
    help_text=_('The PagSeguro URL for test transaction posting.'),
    default="https://localhost:443/security/webpagamentos/webpagto.aspx"),

StringValue(PAYMENT_GROUP,
    'IPN_URL',
    description=_('IPN URL'),
    help_text=_('The PagSeguro URL for IPN.'),
    default="https://pagseguro.uol.com.br/Security/NPI/Default.aspx"),

StringValue(PAYMENT_GROUP,
    'IPN_TEST_URL',
    description=_('IPN URL'),
    help_text=_('The PagSeguro URL for IPN.'),
    default="https://localhost:443/Security/NPI/Default.aspx"),

StringValue(PAYMENT_GROUP,
    'BUSINESS',
    description=_('PagSeguro account email'),
    help_text=_('The email address for your paypal account'),
    default="contato@agencialivre.com.br"),

StringValue(PAYMENT_GROUP,
    'BUSINESS_TEST',
    description=_('Paypal test account email'),
    help_text=_('The email address for testing your paypal account'),
    default="contato@agencialivre.com.br"),

StringValue(PAYMENT_GROUP,
    'RETURN_ADDRESS',
    description=_('Return URL'),
    help_text=_('Where PagSeguro will return the customer after the purchase is complete.  This can be a named url and defaults to the standard checkout success.'),
    default="satchmo_checkout-success"),

BooleanValue(PAYMENT_GROUP,
    'LIVE',
    description=_("Accept real payments"),
    help_text=_("False if you want to be in test mode"),
    default=False),

ModuleValue(PAYMENT_GROUP,
    'MODULE',
    description=_('Implementation module'),
    hidden=True,
    default = 'satchmo_pagseguro.pagseguro'),

StringValue(PAYMENT_GROUP,
    'KEY',
    description=_("Module key"),
    hidden=True,
    default = 'PAGSEGURO'),

StringValue(PAYMENT_GROUP,
    'TOKEN',
    description=_("PagSeguro Token"),
    hidden=True,
    default = '8A0BD42CD7AC4009BAC6BB96FE960D8B'),

StringValue(PAYMENT_GROUP,
    'LABEL',
    description=_('English name for this group on the checkout screens'),
    default = 'PagSeguro',
    help_text = _('This will be passed to the translation utility')),

StringValue(PAYMENT_GROUP,
    'URL_BASE',
    description=_('The url base used for constructing urlpatterns which will use this module'),
    default = '^pagseguro/'),

BooleanValue(PAYMENT_GROUP,
    'EXTRA_LOGGING',
    description=_("Verbose logs"),
    help_text=_("Add extensive logs during post."),
    default=False)
)

PAYMENT_GROUP['TEMPLATE_OVERRIDES'] = {
    'shop/checkout/confirm.html' : 'shop/checkout/pagseguro/confirm.html',
}
