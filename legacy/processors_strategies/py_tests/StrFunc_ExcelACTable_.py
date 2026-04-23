from isd_str_sdk.core import (
    StrFunc_ExcelACTable_UnionLetter_FOREIGN,
    StrFunc_ExcelACTable_UnionLetter_SCHOOL,
    StrFunc_ExcelACTable_UnionLetter_ALLOrg,
    StrFunc_ExcelACTable_UnionLetter_STOPWORD,
)
from .run_strategy_tests import run_str_processor_test


def test001():
    FOREIGN_TESTS = [
        ("University of Münster $AND% University of Žilina", "University of Munster $AND% University of Zilina"),
        ("Benemérita Universidad Autónoma de Puebla", "Benemerita Universidad Autonoma de Puebla"),
        ("Poznań University of Technology", "Poznan University of Technology"),
        ("Eberhard Karls Universität of Tübingen", "Eberhard Karls Universitat of Tubingen"),
        ("Óbuda Católica del Perú Neuchâtel Autónoma Pública", "Obuda Catolica del Peru Neuchatel Autonoma Publica"),
    ]
    run_str_processor_test(
        StrFunc_ExcelACTable_UnionLetter_FOREIGN,
        FOREIGN_TESTS,
        "show_all",
    )

def test002():
    SCHOOL_TESTS = [
        ("Universität universität", "University university"),
        ("Département departamento", "Department department"),
    ]
    run_str_processor_test(
        StrFunc_ExcelACTable_UnionLetter_SCHOOL,
        SCHOOL_TESTS,
        "show_all",
    )

def test003():
    ALL_TESTS = [
        ("assoc asociación société società société società médicale medicina", "association association society society society society medical medical"),
    ]
    run_str_processor_test(
        StrFunc_ExcelACTable_UnionLetter_ALLOrg,
        ALL_TESTS,
        "show_all",
    )

def test004():
    TESTS = [
        ("Northwest A&F University - China", "Northwest A&F University - China"),
        ("SRM Institute of Science & Technology Chennai", "SRM Institute OF Science AND Technology Chennai"),
        ("Henan Institute of Science and Technology", "Henan Institute OF Science AND Technology"),
        ("Jiangsu University of Science && Technology", "Jiangsu University OF Science AND Technology"),
        ("University of Science &&& Technology", "University OF Science &&& Technology"),
    ]
    run_str_processor_test(
        StrFunc_ExcelACTable_UnionLetter_STOPWORD,
        TESTS,
        "show_all",
    )


if __name__ == "__main__":
    # test001()
    # test002()
    # test003()
    test004()
