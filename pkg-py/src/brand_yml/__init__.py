from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, overload

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from ._defs import BrandLightDark
from ._utils import find_project_brand_yml, recurse_dicts_and_models
from ._utils_yaml import yaml_brand as yaml
from .base import BrandBase
from .color import BrandColor
from .file import FileLocation, FileLocationLocal, FileLocationUrl
from .logo import BrandLogo, BrandLogoResource
from .meta import BrandMeta
from .typography import BrandTypography


class Brand(BrandBase):
    """
    Brand guidelines in a class.

    A brand instance encapsulates the color, typography and logo preferences for
    a given brand, typically found in brand guidelines created by a company's
    marketing department. `brand_yml.Brand` organizes this information in a
    common, fully-specified class instance that makes it easy to re-use for
    theming any artifact from websites to data visualizations.

    Unified brand information following the Brand YAML specification. Read brand
    metadata from a YAML file, typically named `_brand.yml`, with
    `brand_yml.Brand.from_yaml` or from a YAML string with
    `brand_yml.Brand.from_yaml_str`. Or create a full brand instance directly
    via this class.
    """

    model_config = ConfigDict(
        extra="ignore",
        revalidate_instances="always",
        validate_assignment=True,
    )

    # TODO @docs: Document Brand attributes
    meta: BrandMeta | None = None
    logo: BrandLogo | BrandLogoResource | None = None
    color: BrandColor | None = None
    typography: BrandTypography | None = None
    defaults: dict[str, Any] | None = None
    path: Path | None = Field(None, exclude=True, repr=False)

    @classmethod
    def from_yaml(cls, path: str | Path):
        """
        Read a Brand YAML file.

        Reads a Brand YAML file or finds and reads a `_brand.yml` file and returns
        a validated :class:`Brand` object.

        Parameters
        ----------
        path
            The path to the Brand YAML file or a directory where `_brand.yml` is
            expected to be found. Typically, you can pass `__file__` from the
            calling script to find `_brand.yml` in the current directory or any of
            its parent directories.

        Returns
        -------
        :
            A validated `brand_yml.Brand` object with all fields populated
            according to the Brand YAML file.

        Raises
        ------
        FileNotFoundError
            Raises a `FileNotFoundError` if no brand configuration file is found
            within the given path. Raises `ValueError` or other validation errors
            from [pydantic](https://docs.pydantic.dev/latest/) if the Brand YAML
            file is invalid.

        Examples
        --------

        ```python
        from brand_yml import Brand

        brand = Brand.from_yaml(__file__)
        brand = Brand.from_yaml("path/to/_brand.yml")
        ```
        """
        return cls.model_validate(read_brand_yml(path, as_data=True))

    @classmethod
    def from_yaml_str(cls, text: str, path: str | Path | None = None):
        """
        Create a Brand instance from a string of YAML.

        Parameters
        ----------
        text
            The text of the Brand YAML file.
        path
            The optional path on disk for supporting files like logos and fonts.

        Returns
        -------
        :
            A validated `brand_yml.Brand` object with all fields populated
            according to the Brand YAML text.

        Raises
        ------
        ValueError
            Raises `ValueError` or other validation errors from
            [pydantic](https://docs.pydantic.dev/latest/) if the Brand YAML file
            is invalid.

        Examples
        --------

        ```{python}
        from brand_yml import Brand

        brand = Brand.from_yaml_str(\"\"\"
        meta:
          name: Brand YAML
        color:
          primary: "#ff0202"
        typography:
          base: Open Sans
        \"\"\")
        ```

        ```{python}
        brand.meta
        ```

        ```{python}
        brand.color.primary
        ```
        """
        data = yaml.load(text)

        if path is not None:
            data["path"] = Path(path).absolute()

        return cls.model_validate(data)

    def model_dump_yaml(
        self,
        stream: Any = None,
        *,
        transform: Any = None,
    ) -> Any:
        """
        Serialize the Brand object to YAML.

        Write the [`brand_yml.Brand`](`brand_yml.Brand`) instance to a string
        or to a file on disk.

        Examples
        --------

        ```{python}
        from brand_yml import Brand

        brand = Brand.from_yaml_str(\"\"\"
        meta:
          name: Brand YAML
        color:
          palette:
            orange: "#ff9a02"
          primary: orange
        typography:
          headings: Raleway
        \"\"\")
        ```

        ::: python-code-preview
        ```{python}
        print(brand.model_dump_yaml())
        ```
        :::

        Parameters
        ----------
        stream
            Passed to `stream` parameter of
            [`ruamel.yaml.YAML.dump`](`ruamel.yaml.YAML.dump`).

        transform
            Passed to `transform` parameter of
            [`ruamel.yaml.YAML.dump`](`ruamel.yaml.YAML.dump`).

        Returns
        -------
        :
            A string with the YAML representation of the `brand` if `stream` is
            `None`. Otherwise, the YAML representation is written to `stream`,
            typically a file.

            Note that the output YAML may not be 100% identical to the input
            `_brand.yml`. The output will contain the fully validated Brand
            instance where default or computed values may be included as well as
            any values resolved during validation, such as colors.
        """

        return yaml.dump(self, stream=stream, transform=transform)

    @model_validator(mode="after")
    def _resolve_typography_colors(self):
        """
        Resolve colors in `typography` using `color`.

        Resolves colors used in `brand.typography` in the `color` or
        `background-color` fields of any typography properties. These values are
        replaced when the brand instance is validated so that values are ready
        to be used by any brand consumers.
        """
        if self.typography is None:
            return self

        color_defs = self.color._color_defs(resolved=True) if self.color else {}
        color_names = [
            k for k in BrandColor.model_fields.keys() if k != "palette"
        ]

        for top_field in self.typography.model_fields.keys():
            typography_node = getattr(self.typography, top_field)

            if not isinstance(typography_node, BaseModel):
                continue

            for typography_node_field in typography_node.model_fields.keys():
                if typography_node_field not in ("color", "background_color"):
                    continue

                value = getattr(typography_node, typography_node_field)
                if value is None or not isinstance(value, str):
                    continue

                is_defined = value in color_defs
                is_theme_color = value in color_names

                if not is_defined:
                    if is_theme_color:
                        raise ValueError(
                            f"`typography.{top_field}.{typography_node_field}` "
                            f"referred to `color.{value}` which is not defined."
                        )
                    else:
                        continue

                setattr(
                    typography_node,
                    typography_node_field,
                    color_defs[value],
                )

        return self

    @field_validator("path", mode="after")
    @classmethod
    def _validate_path_is_absolute(cls, value: Path | None) -> Path | None:
        """
        Ensures that the value of the `path` field is specified absolutely.

        Will also expand user directories and resolve any symlinks.
        """
        if value is None:
            return None

        value = Path(value).expanduser()

        if not value.is_absolute():
            raise ValueError(
                f"brand.path must be an absolute path, not `{value}`."
            )

        return value.resolve()

    @model_validator(mode="after")
    def _set_root_path(self):
        """
        Update the root path of local file locations.

        Updates any fields in `brand_yml.Brand` that are known local file
        locations, i.e. fields that are validated into
        `brand_yml.file.FileLocationLocal` instances, to record the root
        directory. These file paths should be specified (and serialized) as
        relative paths in `_brand.yml`, but any brand consumer will need to be
        able to resolve the file locations to their absolute paths via
        `brand_yml.file.FileLocationLocal.absolute()`.
        """
        path = self.path
        if path is not None:
            recurse_dicts_and_models(
                self,
                pred=lambda value: isinstance(value, FileLocationLocal),
                modify=lambda value: value.set_root_dir(path.parent),
            )

        return self

    @field_validator("logo", mode="before")
    @classmethod
    def _promote_logo_scalar_to_resource(cls, value: Any):
        """
        Take a single path value passed to `brand.logo` and promote it into a
        [`brand_yml.BrandLogoResource`](`brand_yml.BrandLogoResource`).
        """
        if isinstance(value, (str, Path, FileLocation)):
            return {"path": value}
        return value


@overload
def read_brand_yml(
    path: str | Path, as_data: Literal[False] = False
) -> Brand: ...


@overload
def read_brand_yml(path: str | Path, as_data: Literal[True]) -> dict: ...


def read_brand_yml(path: str | Path, as_data: bool = False) -> Brand | dict:
    """
    Read a Brand YAML file.

    Reads a Brand YAML file or finds and reads a project-specific `_brand.yml`
    file and returns a validated `~brand_yml.Brand` instance.

    To find a project-specific `_brand.yaml` file, pass the project directory or
    `__file__` (the path of the current Python script).
    `brand_yml.read_brand_yml` will look in that directory or any parent
    directory for a `_brand.yml`, `brand/_brand.yml` or `_brand/_brand.yml`
    file. Note that it starts the search in the directory passed in and moves
    upward to find the Brand YAML file; it does not search into subdirectories
    of the current directory.

    Parameters
    ----------
    path
        The path to the Brand YAML file or a directory where `_brand.yml` is
        expected to be found. Typically, you can pass `__file__` from the
        calling script to find `_brand.yml` in the current directory or any of
        its parent directories.

    as_data
        When `True`, returns the raw brand data as a dictionary parsed from the
        YAML file. When `False`, returns a validated :class:`Brand` object.

    Returns
    -------
    :
        A validated :class:`brand_yml.Brand` object with all fields populated according to
        the Brand YAML file (`as_data=False`, default) or the raw brand data
        as a dictionary (`as_data=True`).

    Raises
    ------
    FileNotFoundError
        Raises a `FileNotFoundError` if no brand configuration file is found
        within the given path.
    ValueError
        `ValueError` or other validation errors are raised from
        [pydantic](https://docs.pydantic.dev/latest/) if the Brand YAML file is
        invalid.

    Examples
    --------

    ```python
    from brand_yml import read_brand_yml

    brand = read_brand_yml(__file__)
    brand = read_brand_yml("path/to/_brand.yml")
    ```
    """

    path = Path(path).absolute()

    if path.is_dir():
        path = find_project_brand_yml(path)
    elif path.suffix == ".py":
        # allows users to simply pass `__file__`
        path = find_project_brand_yml(path.parent)

    with open(path, "r") as f:
        brand_data = yaml.load(f)

    if not isinstance(brand_data, dict):
        raise ValueError(
            f"Invalid Brand YAML file {str(path)!r}. Must be a dictionary."
        )

    brand_data["path"] = path

    if as_data:
        return brand_data

    return Brand.model_validate(brand_data)


__all__ = [
    "Brand",
    "BrandMeta",
    "BrandLogo",
    "BrandColor",
    "BrandTypography",
    "BrandLightDark",
    "BrandLogoResource",
    "FileLocation",
    "FileLocationLocal",
    "FileLocationUrl",
    "read_brand_yml",
]
