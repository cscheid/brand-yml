from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal, TypeVar, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Discriminator,
    Field,
    RootModel,
    Tag,
    field_validator,
    model_validator,
)

from ._utils import BrandBase

T = TypeVar("T")

SingleOrList = Union[T, list[T]]


BrandTypographyFontStyleType = Literal["normal", "italic"]
BrandTypographyFontWeightNamedType = Literal[
    "thin",
    "extra-light",
    "ultra-light",
    "light",
    "normal",
    "regular",
    "medium",
    "semi-bold",
    "demi-bold",
    "bold",
    "extra-bold",
    "ultra-bold",
    "black",
]
BrandTypographyFontWeightAllType = Union[
    float, int, BrandTypographyFontWeightNamedType
]

BrandTypographyFontWeightSimpleType = Union[
    float, int, Literal["normal", "bold"]
]

# https://developer.mozilla.org/en-US/docs/Web/CSS/font-weight#common_weight_name_mapping
BrandTypographyFontWeightMap = {
    "thin": 100,
    "extra-light": 200,
    "ultra-light": 200,
    "light": 300,
    "normal": 400,
    "regular": 400,
    "medium": 500,
    "semi-bold": 600,
    "demi-bold": 600,
    "bold": 700,
    "extra-bold": 800,
    "ultra-bold": 800,
    "black": 900,
}

# https://developer.mozilla.org/en-US/docs/Web/CSS/@font-face/src#font_formats
FontFormats = {
    ".otc": "collection",
    ".ttc": "collection",
    ".eot": "embedded-opentype",
    ".otf": "opentype",
    ".ttf": "truetype",
    ".svg": "svg",
    ".svgz": "svg",
    ".woff": "woff",
    ".woff2": "woff2",
}


class BrandInvalidFontWeight(ValueError):
    def __init__(self, value: any):
        super().__init__(
            f"Invalid font weight {value!r}. Expected a number divisible "
            + "by 100 and between 100 and 900, or one of "
            + f"{', '.join(BrandTypographyFontWeightMap.keys())}."
        )


class BrandUnsupportedFontFileFormat(ValueError):
    def __init__(self, value: any):
        supported = ("opentype", "truetype", "woff", "woff2")
        super().__init__(
            f"Unsupported font file {value!r}. Expected one of {', '.join(supported)}."
        )


def validate_font_weight(
    value: int | str,
) -> BrandTypographyFontWeightSimpleType:
    if isinstance(value, str):
        if value in ("normal", "bold"):
            return value
        if value in BrandTypographyFontWeightMap:
            return BrandTypographyFontWeightMap[value]

    try:
        value = int(value)
    except ValueError:
        raise BrandInvalidFontWeight(value)

    if value < 100 or value > 900 or value % 100 != 0:
        raise BrandInvalidFontWeight(value)

    return value


class BrandTypographyFontFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str
    family: str
    # These are the formats supported by brand_yaml, not *all* available formats
    format: Literal["opentype", "truetype", "woff", "woff2"] = None
    weight: BrandTypographyFontWeightSimpleType = "normal"
    style: BrandTypographyFontStyleType = "normal"

    @field_validator("weight", mode="before")
    @classmethod
    def validate_weight(cls, value: int | str):
        return validate_font_weight(value)

    @model_validator(mode="before")
    @classmethod
    def validate_format(cls, data: any):
        source = data["source"]
        if Path(source).suffix not in FontFormats:
            raise BrandUnsupportedFontFileFormat(source)

        # Get file extension of `source` using built-in modules
        data["format"] = FontFormats[Path(data["source"]).suffix]

        return data


class BrandTypographyFontGoogle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: Literal["google"] = "google"
    family: str
    weight: SingleOrList[BrandTypographyFontWeightAllType] = [400, 700]
    style: SingleOrList[BrandTypographyFontStyleType] = ["normal", "italic"]
    display: Literal["auto", "block", "swap", "fallback", "optional"] = "auto"

    @field_validator("weight", mode="before")
    @classmethod
    def validate_weight(cls, value: SingleOrList[Union[int, str]]):
        if isinstance(value, list):
            return [validate_font_weight(x) for x in value]
        else:
            return validate_font_weight(value)


def brand_typography_font_discriminator(
    x: dict[str, object] | BrandTypographyFontFile | BrandTypographyFontGoogle,
) -> Literal["google", "file"]:
    if isinstance(x, BrandTypographyFontGoogle):
        return "google"
    elif isinstance(x, BrandTypographyFontFile):
        return "file"

    value = x.get("source")

    if not isinstance(value, str):
        pass
    elif value == "google":
        return "google"
    elif Path(value).suffix:
        return "file"

    raise ValueError(
        "Unsupported font source {value!r}, must be a file path or {'google'!r}."
    )


class BrandNamedColor(RootModel):
    root: str


class BrandTypographyOptionsBase(BrandBase):
    model_config = ConfigDict(populate_by_name=True)

    weight: BrandTypographyFontWeightSimpleType = None
    color: BrandNamedColor = None
    background_color: BrandNamedColor = Field(None, alias="background-color")

    @field_validator("weight", mode="before")
    @classmethod
    def validate_weight(cls, value: int | str):
        return validate_font_weight(value)


class BrandTypographyOptionsGenericText(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    family: str = None
    line_height: float = Field(None, alias="line-height")
    style: SingleOrList[BrandTypographyFontStyleType] = None


class BrandTypographyOptions(
    BrandTypographyOptionsBase,
    BrandTypographyOptionsGenericText,
):
    model_config = ConfigDict(extra="forbid")

    size: str = None


class BrandTypographyOptionsNoSize(
    BrandTypographyOptionsBase,
    BrandTypographyOptionsGenericText,
):
    model_config = ConfigDict(extra="forbid")


class BrandTypographyEmphasis(BrandTypographyOptionsBase):
    model_config = ConfigDict(extra="forbid")


class BrandTypographyLink(BrandTypographyOptionsBase):
    model_config = ConfigDict(extra="forbid")

    decoration: str = None


class BrandTypography(BrandBase):
    font: list[
        Annotated[
            Union[
                Annotated[BrandTypographyFontGoogle, Tag("google")],
                Annotated[BrandTypographyFontFile, Tag("file")],
            ],
            Discriminator(brand_typography_font_discriminator),
        ]
    ] = None
    base: BrandTypographyOptions = None
    headings: BrandTypographyOptionsNoSize = None
    monospace: BrandTypographyOptions = None
    emphasis: BrandTypographyEmphasis = None
    link: BrandTypographyLink = None

    def __repr_args__(self):
        fields = [f for f in self.model_fields.keys()]
        values = [getattr(self, f) for f in fields]
        return ((f, v) for f, v in zip(fields, values) if v is not None)
