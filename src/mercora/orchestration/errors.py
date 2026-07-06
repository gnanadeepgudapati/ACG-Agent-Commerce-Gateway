class CheckoutError(Exception):
    code: str = "CHECKOUT_ERROR"


class CartNotFoundForCheckoutError(CheckoutError):
    code = "CART_NOT_FOUND"


class CartEmptyError(CheckoutError):
    code = "CART_EMPTY"


class OutOfStockError(CheckoutError):
    code = "OUT_OF_STOCK"


class PaymentDeclinedError(CheckoutError):
    code = "PAYMENT_DECLINED"
