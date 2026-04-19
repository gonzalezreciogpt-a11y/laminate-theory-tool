from app.domain.units import m_to_mm, mm_to_m, pa_to_gpa


def test_mm_to_m() -> None:
    assert mm_to_m(1.16) == 0.00116


def test_m_to_mm() -> None:
    assert m_to_mm(0.4) == 400.0


def test_pa_to_gpa() -> None:
    assert pa_to_gpa(6.6152367046165588e10) == 66.15236704616559
