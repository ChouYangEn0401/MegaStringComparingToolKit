## NA回填任務0911有用到
def default_001():
    return {
        "Rules": [
            "OR",
            {
                "ColsCompare": [
                    "OR",
                    {
                        "df1": "B",
                        "df2": "B",
                        "method": [
                            "OR",
                            {
                                "algo": "IN",
                                "standard": 1,
                            },
                        ],
                    },
                    {
                        "df1": "C",
                        "df2": "D",
                        "method": [
                            "OR",
                            {
                                "algo": "IN",
                                "standard": 1,
                            }
                        ],
                    },
                ]
            },
            {
                "ColsCompare": [
                    "AND",
                    {
                        "df1": "A",
                        "df2": "A",
                        "method": [
                            "OR",
                            {
                                "algo": "EXACT",
                                "standard": 1,
                            },
                            {
                                "algo": "FUZZY",
                                "standard": 0.97,
                            },
                            {
                                "algo": "EXACT",
                                "standard": 1,
                            },
                            {
                                "algo": "WordLCS",
                                "standard": 0.93,
                            },
                        ],
                    },
                    {
                        "df1": "C",
                        "df2": "C",
                        "method": [
                            "OR",
                            {
                                "algo": "FUZZY",
                                "standard": 0.97,
                            },
                            {
                                "algo": "WordLCS",
                                "standard": 0.93,
                            }
                        ],
                    },
                    {
                        "df1": "D",
                        "df2": "D",
                        "method": [
                            "OR",
                            {
                                "algo": "EXACT",
                                "standard": 1,
                            }
                        ],
                    },
                ]
            },
        ]
    }

## NA回填任務0911有用到
def TestRealData():
    return {
        "Rules": [
            "OR",
            {
                "ColsCompare": [
                    "OR",
                    {
                        "df1": "[EDIT] Title",
                        "df2": "[EDIT] Title",
                        "method": [
                            "OR",
                            {
                                "algo": "EXACT",
                                "standard": 1,
                            },
                            {
                                "algo": "FUZZY",
                                "standard": 0.95,
                            },
                        ],
                    },
                ]
            },
        ]
    }

## NA回填任務0911有用到
def test_003_error_tracing():
    return {
        "Rules": [
            "OR",
            {
                "ColsCompare": [
                    "AND",
                    {
                        "df1": "[EDIT] Name",
                        "df2": "[EDIT] Name",
                        "method": [
                            "OR",
                            {
                                "algo": "EXACT",
                                "standard": 1,
                            },
                        ],
                    },
                    {
                        "df1": "DOI",
                        "df2": "DOI",
                        "method": [
                            "OR",
                            {
                                "algo": "EXACT",
                                "standard": 1,
                            },
                        ],
                    },
                ]
            },
        ]
    }

## 一級權控清理裡面有用到
def PRIS_Tree():
    return {
        "Rules": [
            "OR",
            {
                "PRIS_Tree": {
                    "df1_col": "Address",
                },
            },
        ]
    }

