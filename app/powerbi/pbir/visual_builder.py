import uuid
from typing import Any


class PBIRVisualBuildError(Exception):
    pass


class PBIRVisualBuilder:
    SCHEMA = (
        "https://developer.microsoft.com/"
        "json-schemas/fabric/item/report/definition/"
        "visualContainer/2.11.0/schema.json"
    )

    TABLE_NAME = "Dataset"

    AGGREGATION_FUNCTIONS = {
        "sum": 0,
        "average": 1,
        "min": 2,
        "max": 3,
        "count": 4,
        "distinct_count": 5,
    }

    def build(
    self,
    element: dict[str, Any],
    tab_order: int,
) -> dict[str, Any]:

        visual_type = element.get("type")

        if visual_type == "card":
            return self._build_card(
                element=element,
                tab_order=tab_order,
            )

        if visual_type == "bar_chart":
            return self._build_categorical_chart(
                element=element,
                tab_order=tab_order,
                pbir_visual_type="clusteredBarChart",
            )

        if visual_type == "column_chart":
            return self._build_categorical_chart(
                element=element,
                tab_order=tab_order,
                pbir_visual_type="clusteredColumnChart",
            )

        if visual_type == "slicer":
            return self._build_slicer(
                element=element,
                tab_order=tab_order,
            )

        if visual_type == "distribution_chart":
            return self._build_distribution_chart(
                element=element,
                tab_order=tab_order,
            )

        raise PBIRVisualBuildError(
            f"Unsupported visual type: {visual_type}"
        )
    
    def _build_card(
        self,
        element: dict[str, Any],
        tab_order: int,
    ) -> dict[str, Any]:

        field = element.get("field")
        aggregation = element.get("aggregation")
        position = element.get("position")

        if not field:
            raise PBIRVisualBuildError(
                "Card requires a field."
            )

        if aggregation not in self.AGGREGATION_FUNCTIONS:
            raise PBIRVisualBuildError(
                f"Unsupported aggregation: {aggregation}"
            )

        if not isinstance(position, dict):
            raise PBIRVisualBuildError(
                "Card requires a position."
            )

        function = self.AGGREGATION_FUNCTIONS[
            aggregation
        ]

        visual_id = self._generate_id()
        filter_id = self._generate_id()

        aggregation_field = self._aggregation_field(
            field=field,
            function=function,
        )

        query_ref = self._query_ref(
            field=field,
            aggregation=aggregation,
        )

        display_name = (
            element.get("title")
            or self._display_name(field)
        )

        return {
            "$schema": self.SCHEMA,
            "name": visual_id,
            "position": {
                "x": position["x"],
                "y": position["y"],
                "z": tab_order,
                "height": position["height"],
                "width": position["width"],
                "tabOrder": tab_order,
            },
            "visual": {
                "visualType": "cardVisual",
                "query": {
                    "queryState": {
                        "Data": {
                            "projections": [
                                {
                                    "field": aggregation_field,
                                    "queryRef": query_ref,
                                    "nativeQueryRef": display_name,
                                    "displayName": display_name,
                                }
                            ]
                        }
                    },
                    "sortDefinition": {
                        "sort": [
                            {
                                "field": aggregation_field,
                                "direction": "Descending",
                            }
                        ],
                        "isDefaultSort": True,
                    },
                },
                "drillFilterOtherVisuals": True,
            },
            "filterConfig": {
                "filters": [
                    {
                        "name": filter_id,
                        "field": aggregation_field,
                        "type": "Advanced",
                    }
                ]
            },
        }

    def _aggregation_field(
        self,
        field: str,
        function: int,
    ) -> dict[str, Any]:

        return {
            "Aggregation": {
                "Expression": {
                    "Column": {
                        "Expression": {
                            "SourceRef": {
                                "Entity": self.TABLE_NAME
                            }
                        },
                        "Property": field,
                    }
                },
                "Function": function,
            }
        }

    def _query_ref(
    self,
    field: str,
    aggregation: str,
) -> str:

            if aggregation == "sum":
                return (
                    f"Sum("
                    f"{self.TABLE_NAME}.{field}"
                    ")"
                )

            if aggregation == "average":
                # Keep this as Sum because this matches the
                # PBIR generated by your Power BI Desktop
                # reference visual for Average.
                return (
                    f"Sum("
                    f"{self.TABLE_NAME}.{field}"
                    ")"
                )

            if aggregation == "min":
                return (
                    f"Min("
                    f"{self.TABLE_NAME}.{field}"
                    ")"
                )

            if aggregation == "max":
                return (
                    f"Max("
                    f"{self.TABLE_NAME}.{field}"
                    ")"
                )

            if aggregation == "count":
                return (
                    f"Count("
                    f"{self.TABLE_NAME}.{field}"
                    ")"
                )

            if aggregation == "distinct_count":
                # Keep this behavior because it matches
                # the reference card PBIR you captured.
                return (
                    f"CountNonNull("
                    f"{self.TABLE_NAME}.{field}"
                    ")"
                )

            raise PBIRVisualBuildError(
                f"Unsupported aggregation: {aggregation}"
            )
    @staticmethod
    def _generate_id() -> str:
        return uuid.uuid4().hex[:20]

    @staticmethod
    def _display_name(
        field: str,
    ) -> str:

        return (
            field
            .replace("_", " ")
            .strip()
            .title()
        )

    def _build_categorical_chart(
            self,
            element: dict[str, Any],
            tab_order: int,
            pbir_visual_type: str,
        ) -> dict[str, Any]:

            category = element.get("category")
            value = element.get("value")
            aggregation = element.get("aggregation")
            position = element.get("position")

            if not category:
                raise PBIRVisualBuildError(
                    "Categorical chart requires a category."
                )

            if not value:
                raise PBIRVisualBuildError(
                    "Categorical chart requires a value."
                )

            if aggregation not in self.AGGREGATION_FUNCTIONS:
                raise PBIRVisualBuildError(
                    f"Unsupported aggregation: {aggregation}"
                )

            if not isinstance(position, dict):
                raise PBIRVisualBuildError(
                    "Categorical chart requires a position."
                )

            function = self.AGGREGATION_FUNCTIONS[
                aggregation
            ]

            visual_id = self._generate_id()
            category_filter_id = self._generate_id()
            value_filter_id = self._generate_id()

            category_field = self._column_field(
                category
            )

            value_field = self._aggregation_field(
                field=value,
                function=function,
            )

            return {
                "$schema": self.SCHEMA,
                "name": visual_id,
                "position": {
                    "x": position["x"],
                    "y": position["y"],
                    "z": tab_order,
                    "height": position["height"],
                    "width": position["width"],
                    "tabOrder": tab_order,
                },
                "visual": {
                    "visualType": pbir_visual_type,
                    "query": {
                        "queryState": {
                            "Category": {
                                "projections": [
                                    {
                                        "field": category_field,
                                        "queryRef": (
                                            f"{self.TABLE_NAME}.{category}"
                                        ),
                                        "nativeQueryRef": category,
                                        "active": True,
                                    }
                                ]
                            },
                            "Y": {
                                "projections": [
                                    {
                                        "field": value_field,
                                        "queryRef": self._query_ref(
                                            field=value,
                                            aggregation=aggregation,
                                        ),
                                        "nativeQueryRef": (
                                            self._native_query_ref(
                                                field=value,
                                                aggregation=aggregation,
                                            )
                                        ),
                                    }
                                ]
                            },
                        },
                        "sortDefinition": {
                            "sort": [
                                {
                                    "field": value_field,
                                    "direction": "Descending",
                                }
                            ],
                            "isDefaultSort": True,
                        },
                    },
                    "drillFilterOtherVisuals": True,
                },
                "filterConfig": {
                    "filters": [
                        {
                            "name": category_filter_id,
                            "field": category_field,
                            "type": "Categorical",
                        },
                        {
                            "name": value_filter_id,
                            "field": value_field,
                            "type": "Advanced",
                        },
                    ]
                },
            }



    def _column_field(
                self,
                field: str,
            ) -> dict[str, Any]:

                return {
                    "Column": {
                        "Expression": {
                            "SourceRef": {
                                "Entity": self.TABLE_NAME
                            }
                        },
                        "Property": field,
                    }
                }


    def _native_query_ref(
    self,
    field: str,
    aggregation: str,
) -> str:

            labels = {
                "sum": "Sum of",
                "average": "Average of",
                "min": "Minimum of",
                "max": "Maximum of",
                "count": "Count of",
                "distinct_count": "Distinct count of",
            }

            label = labels.get(
                aggregation
            )

            if not label:
                return field

            return f"{label} {field}"

    
    def _build_slicer(
    self,
    element: dict[str, Any],
    tab_order: int,
) -> dict[str, Any]:

        field = element.get("field")
        position = element.get("position")

        if not field:
            raise PBIRVisualBuildError(
                "Slicer requires a field."
            )

        if not isinstance(position, dict):
            raise PBIRVisualBuildError(
                "Slicer requires a position."
            )

        visual_id = self._generate_id()
        filter_id = self._generate_id()

        column_field = self._column_field(
            field
        )

        return {
            "$schema": self.SCHEMA,
            "name": visual_id,
            "position": {
                "x": position["x"],
                "y": position["y"],
                "z": tab_order,
                "height": position["height"],
                "width": position["width"],
                "tabOrder": tab_order,
            },
            "visual": {
                "visualType": "slicer",
                "query": {
                    "queryState": {
                        "Values": {
                            "projections": [
                                {
                                    "field": column_field,
                                    "queryRef": (
                                        f"{self.TABLE_NAME}.{field}"
                                    ),
                                    "nativeQueryRef": field,
                                    "active": True,
                                }
                            ]
                        }
                    }
                },
                "objects": {
                    "data": [
                        {
                            "properties": {
                                "mode": {
                                    "expr": {
                                        "Literal": {
                                            "Value": "'Basic'"
                                        }
                                    }
                                }
                            }
                        }
                    ]
                },
                "drillFilterOtherVisuals": True,
            },
            "filterConfig": {
                "filters": [
                    {
                        "name": filter_id,
                        "field": column_field,
                        "type": "Categorical",
                    }
                ]
            },
        }            





    def _build_distribution_chart(
    self,
    element: dict[str, Any],
    tab_order: int,
) -> dict[str, Any]:

        field = element.get("field")
        position = element.get("position")

        if not field:
            raise PBIRVisualBuildError(
                "Distribution chart requires a field."
            )

        if not isinstance(position, dict):
            raise PBIRVisualBuildError(
                "Distribution chart requires a position."
            )

        bin_field = f"{field} Bin"

        visual_id = self._generate_id()
        category_filter_id = self._generate_id()
        value_filter_id = self._generate_id()

        category_field = self._column_field(
            bin_field
        )

        # Count non-null values of the original field.
        function = self.AGGREGATION_FUNCTIONS[
            "count"
        ]

        value_field = self._aggregation_field(
            field=field,
            function=function,
        )

        return {
            "$schema": self.SCHEMA,
            "name": visual_id,
            "position": {
                "x": position["x"],
                "y": position["y"],
                "z": tab_order,
                "height": position["height"],
                "width": position["width"],
                "tabOrder": tab_order,
            },
            "visual": {
                "visualType": "clusteredColumnChart",
                "query": {
                    "queryState": {
                        "Category": {
                            "projections": [
                                {
                                    "field": category_field,
                                    "queryRef": (
                                        f"{self.TABLE_NAME}.{bin_field}"
                                    ),
                                    "nativeQueryRef": bin_field,
                                    "active": True,
                                }
                            ]
                        },
                        "Y": {
                            "projections": [
                                {
                                    "field": value_field,
                                    "queryRef": self._query_ref(
                                        field=field,
                                        aggregation="count",
                                    ),
                                    "nativeQueryRef": (
                                        f"Count of {field}"
                                    ),
                                }
                            ]
                        },
                    },
                    "sortDefinition": {
                        "sort": [
                            {
                                "field": category_field,
                                "direction": "Ascending",
                            }
                        ],
                        "isDefaultSort": True,
                    },
                },
                "drillFilterOtherVisuals": True,
            },
            "filterConfig": {
                "filters": [
                    {
                        "name": category_filter_id,
                        "field": category_field,
                        "type": "Categorical",
                    },
                    {
                        "name": value_filter_id,
                        "field": value_field,
                        "type": "Advanced",
                    },
                ]
            },
        }