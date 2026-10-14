import pytest

from sonartk.map_builder.map_2d.map_canvas import MapCanvas, jagged_edge


class TestJaggedEdge:
    def test_stays_within_amplitude_and_step(self) -> None:
        edge = jagged_edge(500, 50, amplitude=3, seed=1, max_step=2)
        assert len(edge) == 500
        assert all(47 <= value <= 53 for value in edge)
        assert all(abs(b - a) <= 2 for a, b in zip(edge, edge[1:]))

    def test_same_seed_repeats(self) -> None:
        a = jagged_edge(100, 10, amplitude=4, seed=7)
        assert a == jagged_edge(100, 10, amplitude=4, seed=7)
        assert a != jagged_edge(100, 10, amplitude=4, seed=8)

    def test_zero_amplitude_is_flat(self) -> None:
        assert jagged_edge(5, 9, amplitude=0, seed=3) == [9] * 5

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"width": 0, "base": 1, "amplitude": 1},
            {"width": 3, "base": 1, "amplitude": -1},
            {"width": 3, "base": 1, "amplitude": 1, "max_step": 0},
        ],
    )
    def test_rejects_invalid_arguments(self, kwargs: dict) -> None:
        with pytest.raises(ValueError):
            jagged_edge(**kwargs)


class TestMapCanvas:
    def test_rows_are_written_north_first(self) -> None:
        canvas = MapCanvas(3, 2, ".")
        canvas.set((0, 0), "s")
        canvas.set((2, 1), "n")
        assert canvas.to_rows() == ["..n", "s.."]
        assert canvas.get((0, 0)) == "s"
        assert canvas.get((2, 1)) == "n"

    def test_from_rows_round_trips(self) -> None:
        rows = ["~~~", "-s-", "sss"]
        canvas = MapCanvas.from_rows(rows)
        assert (canvas.width, canvas.height) == (3, 3)
        assert canvas.get((1, 1)) == "s"
        assert canvas.get((0, 2)) == "~"
        assert canvas.to_rows() == rows

    @pytest.mark.parametrize("rows", [[], [""], ["ab", "c"]])
    def test_from_rows_rejects_bad_input(self, rows: list[str]) -> None:
        with pytest.raises(ValueError):
            MapCanvas.from_rows(rows)

    def test_fill_rect_is_inclusive_and_order_independent(self) -> None:
        canvas = MapCanvas(4, 3, ".")
        canvas.fill_rect((2, 2), (1, 1), "x")
        assert canvas.to_rows() == [".xx.", ".xx.", "...."]

    def test_fill_between_follows_the_edges_and_clamps(self) -> None:
        canvas = MapCanvas(3, 4, ".")
        canvas.fill_between([0, 1, -5], [2, 2, 99], "w")
        assert canvas.to_rows() == ["..w", "..w", "www", "w.w"]

    def test_fill_between_needs_a_value_per_column(self) -> None:
        canvas = MapCanvas(3, 3, ".")
        with pytest.raises(ValueError, match="3 values"):
            canvas.fill_between([0, 0], [1, 1, 1], "w")

    def test_out_of_bounds_access_is_rejected(self) -> None:
        canvas = MapCanvas(2, 2, ".")
        for bad in [(2, 0), (0, 2), (-1, 0)]:
            with pytest.raises(IndexError):
                canvas.get(bad)
            with pytest.raises(IndexError):
                canvas.set(bad, "x")

    def test_codes_must_be_single_characters(self) -> None:
        with pytest.raises(ValueError, match="single character"):
            MapCanvas(2, 2, "ab")
        canvas = MapCanvas(2, 2, ".")
        with pytest.raises(ValueError):
            canvas.set((0, 0), "")
        with pytest.raises(ValueError):
            canvas.fill_rect((0, 0), (1, 1), "xx")
        with pytest.raises(ValueError):
            canvas.fill_between([0, 0], [1, 1], "xx")

    @pytest.mark.parametrize("size", [(0, 2), (2, 0)])
    def test_rejects_empty_size(self, size: tuple[int, int]) -> None:
        with pytest.raises(ValueError, match="greater than 0"):
            MapCanvas(*size, ".")
