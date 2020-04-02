def test_valid(cldf_dataset, cldf_logger):
    assert cldf_dataset.validate(log=cldf_logger)


def test_forms(cldf_dataset):
    assert len(list(cldf_dataset["FormTable"])) == 3981
    assert any(f["Form"] == "tánpe" for f in cldf_dataset["FormTable"])


def test_parameters(cldf_dataset):
    assert len(list(cldf_dataset["ParameterTable"])) == 199


def test_languages(cldf_dataset):
    assert len(list(cldf_dataset["LanguageTable"])) == 19


def test_cognates(cldf_dataset):
    assert len(list(cldf_dataset["CognateTable"])) == 3769
    assert any(f["Form"] == "porónno" for f in cldf_dataset["CognateTable"])