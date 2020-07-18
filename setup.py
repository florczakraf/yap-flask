from setuptools import find_packages, setup

setup(
    name="yap-flask",
    version="0.2.0-alpha",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=["flask", "flask-sqlalchemy", "flask-alembic",],
    extras_require={"test": ["pytest"]},
)
