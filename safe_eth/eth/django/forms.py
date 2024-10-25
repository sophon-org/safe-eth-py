import binascii
from typing import Any, Optional, Union

from django import forms
from django.core import exceptions
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from hexbytes import HexBytes

from safe_eth.eth.utils import fast_is_checksum_address


class EthereumAddressFieldForm(forms.CharField):
    default_error_messages = {
        "invalid": _("Enter a valid checksummed Ethereum Address."),
    }

    def prepare_value(self, value):
        return value

    def to_python(self, value):
        value = super().to_python(value)
        if value in self.empty_values:
            return None
        elif not fast_is_checksum_address(value):
            raise ValidationError(self.error_messages["invalid"], code="invalid")
        return value


class HexFieldForm(forms.CharField):
    default_error_messages = {
        "invalid": _("Enter a valid hexadecimal."),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.empty_value = None

    def prepare_value(self, value: memoryview) -> str:
        if value:
            return "0x" + bytes(value).hex()
        else:
            return ""

    def to_python(self, value: Optional[Any]) -> Optional[HexBytes]:
        if value in self.empty_values:
            return self.empty_value
        try:
            if isinstance(value, str):
                value = value.strip()
            if isinstance(value, (str, bytes, bytearray, int)):
                return HexBytes(value)
            else:
                raise TypeError(f"Unsupported type for HexBytes: {type(value)}")
        except (binascii.Error, TypeError, ValueError):
            raise exceptions.ValidationError(
                self.error_messages["invalid"],
                code="invalid",
                params={"value": value},
            )


class Keccak256FieldForm(HexFieldForm):
    default_error_messages = {
        "invalid": _('"%(value)s" is not a valid keccak256 hash.'),
        "length": _('"%(value)s" keccak256 hash should be 32 bytes.'),
    }

    def prepare_value(self, value: Union[str, memoryview]) -> str:
        # Keccak field already returns a hex str
        if isinstance(value, str):
            return value
        return super().prepare_value(value)

    def to_python(self, value: Optional[Any]) -> Optional[HexBytes]:
        python_value: Optional[HexBytes] = super().to_python(value)
        if python_value and len(python_value) != 32:
            raise ValidationError(
                self.error_messages["length"],
                code="length",
                params={"value": python_value.hex()},
            )
        return python_value
