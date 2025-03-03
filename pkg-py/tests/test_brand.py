import tempfile
from pathlib import Path

import pytest
from brand_yml import Brand, read_brand_yml
from brand_yml.file import FileLocationLocal
from brand_yml.logo import BrandLogo, BrandLogoResource
from brand_yml.typography import BrandTypography, BrandTypographyFontFiles

path_fixtures = Path(__file__).parent / "fixtures"


def test_brand_yml_found_in_dir():
    path = path_fixtures / "find-brand-yml" / "_brand.yml"

    brand_direct = Brand.from_yaml(path)
    brand_found = read_brand_yml(path.parent)

    assert brand_found == brand_direct


def test_brand_yml_found_in_subdir():
    path = path_fixtures / "find-brand-dir" / "empty.py"

    brand_direct = Brand.from_yaml(path.parent / "brand" / "_brand.yml")
    brand_found = read_brand_yml(path)

    assert brand_found == brand_direct


def test_brand_yml_found_from_py_file():
    path = Path(__file__).parent / "fixtures" / "find-brand-yml" / "_brand.yml"

    brand_direct = read_brand_yml(path)
    # Equivalent to passing __file__ from inside empty.py
    brand_found = read_brand_yml(path.parent / "empty.py")

    assert brand_found == brand_direct


def test_brand_yml_not_found_error():
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(FileNotFoundError):
            read_brand_yml(tmpdir)


def test_brand_yml_paths():
    path = path_fixtures / "path-resolution"

    # This doesn't error, even though it points to missing files
    brand = read_brand_yml(path)

    assert isinstance(brand.logo, BrandLogo)
    assert isinstance(brand.logo.small, BrandLogoResource)
    assert isinstance(brand.logo.small.path, FileLocationLocal)

    assert isinstance(brand.typography, BrandTypography)
    assert isinstance(brand.typography.fonts, list)
    assert isinstance(brand.typography.fonts[0], BrandTypographyFontFiles)
    assert isinstance(
        brand.typography.fonts[0].files[0].path, FileLocationLocal
    )

    # Paths are all relative
    assert brand.logo.small.path.root == Path("does-not-exist.png")
    assert brand.logo.small.path.root == brand.logo.small.path.relative()

    assert brand.typography.fonts[0].files[0].path.root == Path("Invisible.ttf")
    assert (
        brand.typography.fonts[0].files[0].path.root
        == brand.typography.fonts[0].files[0].path.relative()
    )

    # Paths can be accessed absolutely
    assert (
        brand.logo.small.path.absolute()
        == (path / "does-not-exist.png").absolute()
    )
    assert (
        brand.typography.fonts[0].files[0].path.absolute()
        == (path / "Invisible.ttf").absolute()
    )

    # These files don't exist, which can be verified
    assert not brand.logo.small.path.exists()
    assert not brand.typography.fonts[0].files[0].path.exists()

    # Updating brand.path updates the paths in the brand -----------------------
    brand.path = path_fixtures / "_brand.yml"

    # Paths are still all relative
    assert brand.logo.small.path.root == Path("does-not-exist.png")
    assert brand.logo.small.path.root == brand.logo.small.path.relative()

    assert brand.typography.fonts[0].files[0].path.root == Path("Invisible.ttf")
    assert (
        brand.typography.fonts[0].files[0].path.root
        == brand.typography.fonts[0].files[0].path.relative()
    )

    # Absolute paths have now been updated
    assert (
        brand.logo.small.path.absolute()
        == (path_fixtures / "does-not-exist.png").absolute()
    )
    assert (
        brand.typography.fonts[0].files[0].path.absolute()
        == (path_fixtures / "Invisible.ttf").absolute()
    )

    # brand.path must be absolute
    with pytest.raises(ValueError):
        brand.path = Path("_brand.yml")
