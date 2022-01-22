# Alchemical change log

**Release 0.5.1** - 2022-01-22

- add update() and delete() to db.Model class ([commit](https://github.com/miguelgrinberg/alchemical/commit/818c0542ec6fc62e14679dd0917d145cb4b19582))
- Documentation on many common use cases ([commit](https://github.com/miguelgrinberg/alchemical/commit/9ade0914da50c9dafbb6595ac271b248af93d660))

**Release 0.5.0** - 2021-10-03

- Add BaseModel.select() convenience method ([commit](https://github.com/miguelgrinberg/alchemical/commit/5c87a2382c2b91edc8fc529d8c7e38c898c2655d))
- Support for pydantic models through SQLModel ([commit](https://github.com/miguelgrinberg/alchemical/commit/73708437d89b846cf16a63b954ba6a569fd5b591))
- Allow `url` argument to be `None` when `binds` is not `None` ([commit](https://github.com/miguelgrinberg/alchemical/commit/3acde22d3b975eece4e43cee74d5886bf5048e92))
- Remove auto-imported SQLAlchemy symbols ([commit](https://github.com/miguelgrinberg/alchemical/commit/5c87a2382c2b91edc8fc529d8c7e38c898c2655d))
- Use session.scalars() and session.scalar() in examples and documentation ([commit](https://github.com/miguelgrinberg/alchemical/commit/cb6e4cd7837e686db51f080e8203a404f5d93e65))

**Release 0.4.0** - 2021-08-18

- Added db.session similar to Flask-SQLAlchemy ([commit](https://github.com/miguelgrinberg/alchemical/commit/a66f9bdac6a45aefb71fbc229598a1779f6e3f1e))
- Add a run_sync method to the asyncio class ([commit](https://github.com/miguelgrinberg/alchemical/commit/095ff759b48499328e1a53b0b048eb59701ad37b))
- Use a separate Metadata for each bind ([commit](https://github.com/miguelgrinberg/alchemical/commit/5cdb37d85243e2350c61922c5d1ab8df15076c09))
- Raise an error when the database URL is not configured. ([commit](https://github.com/miguelgrinberg/alchemical/commit/d3f3787a19e271c9cac6bca76fd17201b5c59ea2))
- flaskr and aioflaskr examples ported from the Flask official tutorial

**Release 0.3.0** - 2021-08-03

- Add support for aioflask ([commit](https://github.com/miguelgrinberg/alchemical/commit/f5c0e2b424b39ab129789c2e707d49ecfb117b13))
- Added a "How do I ...?" to the documentation ([commit](https://github.com/miguelgrinberg/alchemical/commit/6c1659f9041ad1bac14bb87c6c1cc7fa929f6622))
- Documentation updates ([commit](https://github.com/miguelgrinberg/alchemical/commit/fc13d12bd9014a7fa56f42c61012e08a85497c76))
- Example updates ([commit](https://github.com/miguelgrinberg/alchemical/commit/6d48822d069386d8bf4529b90ef678695faae158))
- aioflask examples ([commit](https://github.com/miguelgrinberg/alchemical/commit/d4d196eabf0687b909de112291d71950f61a9096))
- Remaining unit tests ([commit](https://github.com/miguelgrinberg/alchemical/commit/7fdb15a10a80dc4c01642cff35f22985761abbcd))

**Release 0.2.0** - 2021-07-06

- Asyncio support ([commit](https://github.com/miguelgrinberg/alchemical/commit/1890ced7c2b60a8d165dd02a7a8762bcc4a2cad1))
- Fix database URLs when needed ([commit](https://github.com/miguelgrinberg/alchemical/commit/e3c081f12c3b9e7838aee3134ede428ff92eb5b8))
- First batch of unit tests ([commit](https://github.com/miguelgrinberg/alchemical/commit/f56ea2ed446ada135d81fd9a4046f0bc78d871f0))
- Documentation ([commit](https://github.com/miguelgrinberg/alchemical/commit/09eb1c724ec501b2a25807e46a8b603a13c23668))
- Build setup ([commit](https://github.com/miguelgrinberg/alchemical/commit/cff9de37a363f604aa5048cc8005c21f234e9cfd))

**Release 0.1.0** - 2021-05-30

- Add engine options ([commit](https://github.com/miguelgrinberg/alchemical/commit/c3e551739ff8ae02fa79fd2da788127aaf264bf2))
- First commit ([commit](https://github.com/miguelgrinberg/alchemical/commit/7f58f7ba7783011d6977d6cab3cb952305aacbf1))
