from typing import Any


class DashboardRanking:
    """
    Rank measures and dimensions according to their
    business importance.

    This ranking is later consumed by the KPI selector,
    visual selector and dashboard planner.
    """

    MEASURE_PRIORITY = {
        "revenue": 100,
        "sales": 100,
        "profit": 100,
        "amount": 95,
        "income": 95,
        "cost": 90,
        "expense": 90,
        "score": 95,
        "marks": 95,
        "grade": 95,
        "attendance": 90,
        "study": 90,
        "sleep": 85,
        "screen": 80,
        "exercise": 80,
        "water": 70,
        "rating": 85,
        "age": 70,
        "duration": 75,
        "time": 75,
        "quantity": 85,
        "count": 80,
        "distance": 75,
        "height": 70,
        "weight": 70,
    }

    DIMENSION_PRIORITY = {
        "department": 100,
        "category": 100,
        "segment": 100,
        "region": 95,
        "country": 95,
        "state": 90,
        "city": 85,
        "course": 95,
        "class": 90,
        "semester": 90,
        "study_mode": 90,
        "study mode": 90,
        "gender": 85,
        "occupation": 80,
        "customer": 75,
        "product": 75,
    }

    def rank_measures(
        self,
        measures: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        return sorted(
            measures,
            key=self._measure_score,
            reverse=True,
        )

    def rank_dimensions(
        self,
        dimensions: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        return sorted(
            dimensions,
            key=self._dimension_score,
            reverse=True,
        )

    def _measure_score(
        self,
        measure: dict[str, Any],
    ) -> int:

        name = measure["name"].lower()

        score = 50

        for keyword, value in self.MEASURE_PRIORITY.items():
            if keyword in name:
                score = max(score, value)

        return score

    def _dimension_score(
        self,
        dimension: dict[str, Any],
    ) -> int:

        name = dimension["name"].lower()

        score = 50

        for keyword, value in self.DIMENSION_PRIORITY.items():
            if keyword in name:
                score = max(score, value)

        return score