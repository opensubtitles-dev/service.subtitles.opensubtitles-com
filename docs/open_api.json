{
    "openapi": "3.0.3",
    "info": {
        "title": "OpenSubtitles API",
        "description": "Explore Open Subtitles API here",
        "contact": {
            "name": "OpenSubtitles API Support",
            "url": "https://www.opensubtitles.com/en/contact/",
            "email": "support@opensubtitles.org"
        },
        "license": {
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT"
        },
        "version": "1.0.1",
        "termsOfService": "https://www.opensubtitles.com/en/tos/"
    },
    "servers": [
        {
            "url": "https://api.opensubtitles.com/api/v1",
            "description": "Default server"
        },
        {
            "url": "https://vip-api.opensubtitles.com/api/v1",
            "description": "VIP server"
        }
    ],
    "tags": [
        {
            "name": "AI Transcribe",
            "description": "AI Transcribe - lists APIs and supported Languages"
        },
        {
            "name": "AI Transcription",
            "description": "AI Transcription process media to generate subtitles"
        },
        {
            "name": "AI Translate",
            "description": "AI Translate - lists APIs and supported Languages"
        },
        {
            "name": "AI Translation",
            "description": "AI Translation from one language to another one"
        },
        {
            "name": "Authentication",
            "description": "Authentification of user"
        },
        {
            "name": "Discover",
            "description": "Discover popular, latest and most downloaded subtitles"
        },
        {
            "name": "Download",
            "description": "Download of subtitles"
        },
        {
            "name": "Features",
            "description": "Search for feature"
        },
        {
            "name": "Infos",
            "description": "General API infos"
        },
        {
            "name": "Subtitles",
            "description": "Subtitles search for a specific release"
        },
        {
            "name": "User",
            "description": "User operations"
        },
        {
            "name": "Utilities",
            "description": "Various utilities"
        }
    ],
    "paths": {
        "/login": {
            "post": {
                "tags": [
                    "Authentication"
                ],
                "summary": "Login",
                "description": "Create a token to authenticate a user. If response code is ```401 Unathorized``` stop sending further requests with the same credentials, login is \"expensive\" operation.\n\nRequest rate limit is 1 request per 1 second, 10 requests per minute and 30 requests per hour because some clients just endlessly sending wrong credentials in loop.\n\nFurther API requests must continue on returned ```base_url``` host, which can have different cache time for search results and different request rate limits. If ```base_url``` equals ```vip-api.opensubtitles.com``` make sure you always send with every request JWT token (if available), otherwise request might fail with 4xx code.",
                "operationId": "login",
                "parameters": [
                    {
                        "name": "Content-Type",
                        "in": "header",
                        "description": "application/json",
                        "required": true,
                        "schema": {
                            "type": "string",
                            "default": "application/json"
                        }
                    },
                    {
                        "schema": {
                            "type": "string"
                        },
                        "in": "header",
                        "name": "User-Agent",
                        "description": "<<{{APP_NAME}} v{{APP_VERSION}}>>"
                    }
                ],
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "x-examples": {
                                    "example": {
                                        "username": "",
                                        "password": ""
                                    }
                                },
                                "properties": {
                                    "username": {
                                        "type": "string"
                                    },
                                    "password": {
                                        "type": "string"
                                    }
                                },
                                "required": [
                                    "username",
                                    "password"
                                ]
                            }
                        }
                    },
                    "required": false
                },
                "responses": {
                    "200": {
                        "description": "Create session and token",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "user": {
                                            "type": "object",
                                            "required": [
                                                "allowed_translations",
                                                "allowed_downloads",
                                                "level",
                                                "user_id",
                                                "ext_installed",
                                                "vip"
                                            ],
                                            "properties": {
                                                "allowed_translations": {
                                                    "type": "number"
                                                },
                                                "allowed_downloads": {
                                                    "type": "number"
                                                },
                                                "level": {
                                                    "minLength": 1,
                                                    "type": "string",
                                                    "example": "VIP Member"
                                                },
                                                "user_id": {
                                                    "type": "number"
                                                },
                                                "ext_installed": {
                                                    "type": "boolean"
                                                },
                                                "vip": {
                                                    "type": "boolean"
                                                }
                                            }
                                        },
                                        "base_url": {
                                            "type": "string",
                                            "format": "hostname",
                                            "default": "api.opensubtitles.com",
                                            "example": "api.opensubtitles.com",
                                            "enum": [
                                                "api.opensubtitles.com",
                                                "vip-api.opensubtitles.com"
                                            ]
                                        },
                                        "token": {
                                            "minLength": 1,
                                            "type": "string"
                                        },
                                        "status": {
                                            "type": "number"
                                        }
                                    },
                                    "required": [
                                        "user",
                                        "base_url",
                                        "token",
                                        "status"
                                    ]
                                },
                                "example": {
                                    "user": {
                                        "allowed_downloads": 100,
                                        "allowed_translations": 5,
                                        "level": "Sub leecher",
                                        "user_id": 66,
                                        "ext_installed": false,
                                        "vip": false
                                    },
                                    "base_url": "api.opensubtitles.com",
                                    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJEOU5aaWUyVjhWOU1hTnJVZWVvcEEwWUNoWEt6Wkx3NiIsImV4cCI6MTYwNDM1ODAwMH0.sMibjAFnkcs-HJ4zhdCwBeGrZ_UvzMbgl5NxYV2uALM",
                                    "status": 200
                                }
                            }
                        }
                    }
                },
                "deprecated": false,
                "security": [
                    {
                        "Api-Key": []
                    }
                ]
            }
        },
        "/logout": {
            "delete": {
                "tags": [
                    "Authentication"
                ],
                "summary": "Logout",
                "description": "Destroy a user token to end a session. Bearer token is required for this endpoint.",
                "operationId": "logout",
                "responses": {
                    "200": {
                        "description": "Destroy session and current token",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object"
                                },
                                "example": {
                                    "message": "token successfully destroyed",
                                    "status": 200
                                }
                            }
                        }
                    }
                },
                "deprecated": false,
                "security": [
                    {
                        "Bearer": []
                    },
                    {
                        "Api-Key": []
                    }
                ],
                "parameters": [
                    {
                        "schema": {
                            "type": "string"
                        },
                        "in": "header",
                        "name": "User-Agent",
                        "description": "<<{{APP_NAME}} v{{APP_VERSION}}>>"
                    }
                ]
            }
        },
        "/infos/formats": {
            "get": {
                "tags": [
                    "Infos"
                ],
                "summary": "Subtitle Formats",
                "description": "List subtitle formats recognized by the API  ",
                "operationId": "formats",
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "description": "",
                                    "type": "object",
                                    "x-examples": {
                                        "example-1": {
                                            "data": {
                                                "output_formats": [
                                                    "srt",
                                                    "sub",
                                                    "mpl",
                                                    "webvtt",
                                                    "dfxp",
                                                    "txt"
                                                ]
                                            }
                                        }
                                    },
                                    "properties": {
                                        "data": {
                                            "type": "object",
                                            "required": [
                                                "output_formats"
                                            ],
                                            "properties": {
                                                "output_formats": {
                                                    "type": "array",
                                                    "items": {}
                                                }
                                            }
                                        }
                                    },
                                    "required": [
                                        "data"
                                    ]
                                },
                                "examples": {
                                    "example": {
                                        "value": {
                                            "data": {
                                                "output_formats": [
                                                    "srt",
                                                    "sub",
                                                    "mpl",
                                                    "webvtt",
                                                    "dfxp",
                                                    "txt"
                                                ]
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "deprecated": false,
                "security": [
                    {
                        "Api-Key": []
                    }
                ],
                "parameters": [
                    {
                        "schema": {
                            "type": "string"
                        },
                        "in": "header",
                        "name": "User-Agent",
                        "description": "<<{{APP_NAME}} v{{APP_VERSION}}>>"
                    }
                ]
            }
        },
        "/infos/languages": {
            "get": {
                "tags": [
                    "Infos"
                ],
                "summary": "Languages",
                "description": "Get the languages information",
                "operationId": "languages",
                "responses": {
                    "200": {
                        "description": "Get the languages table containing the codes and names used through the API",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "required": [
                                        "data"
                                    ],
                                    "type": "object",
                                    "properties": {
                                        "data": {
                                            "minItems": 1,
                                            "uniqueItems": true,
                                            "type": "array",
                                            "items": {
                                                "required": [
                                                    "language_code",
                                                    "language_name"
                                                ],
                                                "type": "object",
                                                "properties": {
                                                    "language_code": {
                                                        "minLength": 1,
                                                        "type": "string"
                                                    },
                                                    "language_name": {
                                                        "minLength": 1,
                                                        "type": "string"
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    "description": ""
                                },
                                "example": {
                                    "data": [
                                        {
                                            "language_code": "af",
                                            "language_name": "Afrikaans"
                                        },
                                        {
                                            "language_code": "sq",
                                            "language_name": "Albanian"
                                        },
                                        {
                                            "language_code": "ar",
                                            "language_name": "Arabic"
                                        },
                                        {
                                            "language_code": "an",
                                            "language_name": "Aragonese"
                                        },
                                        {
                                            "language_code": "hy",
                                            "language_name": "Armenian"
                                        },
                                        {
                                            "language_code": "at",
                                            "language_name": "Asturian"
                                        },
                                        {
                                            "language_code": "eu",
                                            "language_name": "Basque"
                                        },
                                        {
                                            "language_code": "be",
                                            "language_name": "Belarusian"
                                        },
                                        {
                                            "language_code": "bn",
                                            "language_name": "Bengali"
                                        },
                                        {
                                            "language_code": "bs",
                                            "language_name": "Bosnian"
                                        },
                                        {
                                            "language_code": "br",
                                            "language_name": "Breton"
                                        },
                                        {
                                            "language_code": "bg",
                                            "language_name": "Bulgarian"
                                        },
                                        {
                                            "language_code": "my",
                                            "language_name": "Burmese"
                                        },
                                        {
                                            "language_code": "ca",
                                            "language_name": "Catalan"
                                        },
                                        {
                                            "language_code": "zh-cn",
                                            "language_name": "Chinese (simplified)"
                                        },
                                        {
                                            "language_code": "cs",
                                            "language_name": "Czech"
                                        },
                                        {
                                            "language_code": "da",
                                            "language_name": "Danish"
                                        },
                                        {
                                            "language_code": "nl",
                                            "language_name": "Dutch"
                                        },
                                        {
                                            "language_code": "en",
                                            "language_name": "English"
                                        },
                                        {
                                            "language_code": "eo",
                                            "language_name": "Esperanto"
                                        },
                                        {
                                            "language_code": "et",
                                            "language_name": "Estonian"
                                        },
                                        {
                                            "language_code": "fi",
                                            "language_name": "Finnish"
                                        },
                                        {
                                            "language_code": "fr",
                                            "language_name": "French"
                                        },
                                        {
                                            "language_code": "ka",
                                            "language_name": "Georgian"
                                        },
                                        {
                                            "language_code": "de",
                                            "language_name": "German"
                                        },
                                        {
                                            "language_code": "gl",
                                            "language_name": "Galician"
                                        },
                                        {
                                            "language_code": "el",
                                            "language_name": "Greek"
                                        },
                                        {
                                            "language_code": "he",
                                            "language_name": "Hebrew"
                                        },
                                        {
                                            "language_code": "hi",
                                            "language_name": "Hindi"
                                        },
                                        {
                                            "language_code": "hr",
                                            "language_name": "Croatian"
                                        },
                                        {
                                            "language_code": "hu",
                                            "language_name": "Hungarian"
                                        },
                                        {
                                            "language_code": "is",
                                            "language_name": "Icelandic"
                                        },
                                        {
                                            "language_code": "id",
                                            "language_name": "Indonesian"
                                        },
                                        {
                                            "language_code": "it",
                                            "language_name": "Italian"
                                        },
                                        {
                                            "language_code": "ja",
                                            "language_name": "Japanese"
                                        },
                                        {
                                            "language_code": "kk",
                                            "language_name": "Kazakh"
                                        },
                                        {
                                            "language_code": "km",
                                            "language_name": "Khmer"
                                        },
                                        {
                                            "language_code": "ko",
                                            "language_name": "Korean"
                                        },
                                        {
                                            "language_code": "lv",
                                            "language_name": "Latvian"
                                        },
                                        {
                                            "language_code": "lt",
                                            "language_name": "Lithuanian"
                                        },
                                        {
                                            "language_code": "lb",
                                            "language_name": "Luxembourgish"
                                        },
                                        {
                                            "language_code": "mk",
                                            "language_name": "Macedonian"
                                        },
                                        {
                                            "language_code": "ml",
                                            "language_name": "Malayalam"
                                        },
                                        {
                                            "language_code": "ms",
                                            "language_name": "Malay"
                                        },
                                        {
                                            "language_code": "ma",
                                            "language_name": "Manipuri"
                                        },
                                        {
                                            "language_code": "mn",
                                            "language_name": "Mongolian"
                                        },
                                        {
                                            "language_code": "no",
                                            "language_name": "Norwegian"
                                        },
                                        {
                                            "language_code": "oc",
                                            "language_name": "Occitan"
                                        },
                                        {
                                            "language_code": "fa",
                                            "language_name": "Persian"
                                        },
                                        {
                                            "language_code": "pl",
                                            "language_name": "Polish"
                                        },
                                        {
                                            "language_code": "pt-pt",
                                            "language_name": "Portuguese"
                                        },
                                        {
                                            "language_code": "ru",
                                            "language_name": "Russian"
                                        },
                                        {
                                            "language_code": "sr",
                                            "language_name": "Serbian"
                                        },
                                        {
                                            "language_code": "si",
                                            "language_name": "Sinhalese"
                                        },
                                        {
                                            "language_code": "sk",
                                            "language_name": "Slovak"
                                        },
                                        {
                                            "language_code": "sl",
                                            "language_name": "Slovenian"
                                        },
                                        {
                                            "language_code": "es",
                                            "language_name": "Spanish"
                                        },
                                        {
                                            "language_code": "sw",
                                            "language_name": "Swahili"
                                        },
                                        {
                                            "language_code": "sv",
                                            "language_name": "Swedish"
                                        },
                                        {
                                            "language_code": "sy",
                                            "language_name": "Syriac"
                                        },
                                        {
                                            "language_code": "ta",
                                            "language_name": "Tamil"
                                        },
                                        {
                                            "language_code": "te",
                                            "language_name": "Telugu"
                                        },
                                        {
                                            "language_code": "tl",
                                            "language_name": "Tagalog"
                                        },
                                        {
                                            "language_code": "th",
                                            "language_name": "Thai"
                                        },
                                        {
                                            "language_code": "tr",
                                            "language_name": "Turkish"
                                        },
                                        {
                                            "language_code": "uk",
                                            "language_name": "Ukrainian"
                                        },
                                        {
                                            "language_code": "ur",
                                            "language_name": "Urdu"
                                        },
                                        {
                                            "language_code": "uz",
                                            "language_name": "Uzbek"
                                        },
                                        {
                                            "language_code": "vi",
                                            "language_name": "Vietnamese"
                                        },
                                        {
                                            "language_code": "ro",
                                            "language_name": "Romanian"
                                        },
                                        {
                                            "language_code": "pt-br",
                                            "language_name": "Portuguese (Brazilian)"
                                        },
                                        {
                                            "language_code": "me",
                                            "language_name": "Montenegrin"
                                        },
                                        {
                                            "language_code": "zh-tw",
                                            "language_name": "Chinese (traditional)"
                                        },
                                        {
                                            "language_code": "ze",
                                            "language_name": "Chinese bilingual"
                                        }
                                    ]
                                }
                            }
                        }
                    }
                },
                "deprecated": false,
                "security": [
                    {
                        "Api-Key": []
                    }
                ],
                "parameters": [
                    {
                        "schema": {
                            "type": "string"
                        },
                        "in": "header",
                        "name": "User-Agent",
                        "description": "<<{{APP_NAME}} v{{APP_VERSION}}>>"
                    }
                ]
            },
            "servers": []
        },
        "/infos/user": {
            "get": {
                "summary": "User Informations",
                "description": "Gather informations about the user authenticated by a bearer token. User information are already sent when user is authenticated, and the remaining downloads is returned with each download, but you can also get these information here.",
                "operationId": "userinfo",
                "responses": {
                    "200": {
                        "description": "Get user data",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": [
                                        "data"
                                    ],
                                    "properties": {
                                        "data": {
                                            "type": "object",
                                            "required": [
                                                "allowed_downloads",
                                                "level",
                                                "user_id",
                                                "vip",
                                                "downloads_count",
                                                "remaining_downloads"
                                            ],
                                            "properties": {
                                                "allowed_downloads": {
                                                    "type": "number"
                                                },
                                                "level": {
                                                    "minLength": 1,
                                                    "type": "string"
                                                },
                                                "user_id": {
                                                    "type": "number"
                                                },
                                                "vip": {
                                                    "type": "boolean"
                                                },
                                                "downloads_count": {
                                                    "type": "number"
                                                },
                                                "remaining_downloads": {
                                                    "type": "number"
                                                }
                                            }
                                        }
                                    }
                                },
                                "example": {
                                    "data": {
                                        "allowed_downloads": 100,
                                        "level": "Sub leecher",
                                        "user_id": 66,
                                        "ext_installed": false,
                                        "vip": false,
                                        "downloads_count": 1,
                                        "remaining_downloads": 99
                                    }
                                }
                            }
                        }
                    }
                },
                "deprecated": false,
                "security": [
                    {
                        "Bearer": []
                    },
                    {
                        "Api-Key": []
                    }
                ],
                "parameters": [
                    {
                        "schema": {
                            "type": "string"
                        },
                        "in": "header",
                        "name": "User-Agent",
                        "description": "<<{{APP_NAME}} v{{APP_VERSION}}>>"
                    }
                ],
                "tags": [
                    "User"
                ]
            }
        },
        "/discover/popular": {
            "get": {
                "tags": [
                    "Discover"
                ],
                "summary": "Popular features",
                "description": "Discover popular features on opensubtitles.com, according to last 30 days downloads.",
                "operationId": "popular",
                "parameters": [
                    {
                        "name": "language",
                        "in": "query",
                        "description": "Language code, 1 language per query, or \"all\"",
                        "schema": {
                            "type": "string"
                        }
                    },
                    {
                        "name": "type",
                        "in": "query",
                        "description": "Type (movie or tvshow)",
                        "schema": {
                            "type": "string"
                        }
                    },
                    {
                        "schema": {
                            "type": "string"
                        },
                        "in": "header",
                        "name": "User-Agent",
                        "description": "<<{{APP_NAME}} v{{APP_VERSION}}>>"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/Subtitle"
                                }
                            }
                        }
                    }
                },
                "deprecated": false,
                "security": [
                    {
                        "Api-Key": []
                    }
                ]
            }
        },
        "/discover/latest": {
            "get": {
                "tags": [
                    "Discover"
                ],
                "summary": "Latest subtitles",
                "description": "Lists 60 latest uploaded subtitles",
                "operationId": "latest",
                "parameters": [
                    {
                        "name": "language",
                        "in": "query",
                        "description": "Language code, 1 language per query, or \"all\"",
                        "schema": {
                            "type": "string"
                        }
                    },
                    {
                        "name": "type",
                        "in": "query",
                        "description": "Type (movie or tvshow)",
                        "schema": {
                            "type": "string"
                        }
                    },
                    {
                        "schema": {
                            "type": "string"
                        },
                        "in": "header",
                        "name": "User-Agent",
                        "description": "<<{{APP_NAME}} v{{APP_VERSION}}>>"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "required": [
                                        "data",
                                        "page",
                                        "total_count",
                                        "total_pages"
                                    ],
                                    "type": "object",
                                    "properties": {
                                        "total_pages": {
                                            "type": "number"
                                        },
                                        "total_count": {
                                            "type": "number"
                                        },
                                        "page": {
                                            "type": "number"
                                        },
                                        "data": {
                                            "minItems": 1,
                                            "uniqueItems": true,
                                            "type": "array",
                                            "items": {
                                                "required": [
                                                    "id",
                                                    "type"
                                                ],
                                                "type": "object",
                                                "properties": {
                                                    "id": {
                                                        "minLength": 1,
                                                        "type": "string"
                                                    },
                                                    "type": {
                                                        "minLength": 1,
                                                        "type": "string"
                                                    },
                                                    "attributes": {
                                                        "required": [
                                                            "ai_translated",
                                                            "comments",
                                                            "download_count",
                                                            "feature_details",
                                                            "files",
                                                            "foreign_parts_only",
                                                            "fps",
                                                            "from_trusted",
                                                            "hd",
                                                            "hearing_impaired",
                                                            "language",
                                                            "legacy_subtitle_id",
                                                            "new_download_count",
                                                            "points",
                                                            "ratings",
                                                            "related_links",
                                                            "release",
                                                            "subtitle_id",
                                                            "upload_date",
                                                            "uploader",
                                                            "url",
                                                            "votes"
                                                        ],
                                                        "type": "object",
                                                        "properties": {
                                                            "subtitle_id": {
                                                                "minLength": 1,
                                                                "type": "string"
                                                            },
                                                            "language": {
                                                                "minLength": 1,
                                                                "type": "string"
                                                            },
                                                            "download_count": {
                                                                "type": "number"
                                                            },
                                                            "new_download_count": {
                                                                "type": "number"
                                                            },
                                                            "hearing_impaired": {
                                                                "type": "boolean"
                                                            },
                                                            "hd": {
                                                                "type": "boolean"
                                                            },
                                                            "format": {
                                                                "type": "object"
                                                            },
                                                            "fps": {
                                                                "type": "number"
                                                            },
                                                            "votes": {
                                                                "type": "number"
                                                            },
                                                            "points": {
                                                                "type": "number"
                                                            },
                                                            "ratings": {
                                                                "type": "number"
                                                            },
                                                            "from_trusted": {
                                                                "type": "boolean"
                                                            },
                                                            "foreign_parts_only": {
                                                                "type": "boolean"
                                                            },
                                                            "ai_translated": {
                                                                "type": "boolean"
                                                            },
                                                            "machine_translated": {
                                                                "type": "object"
                                                            },
                                                            "upload_date": {
                                                                "minLength": 1,
                                                                "type": "string"
                                                            },
                                                            "release": {
                                                                "minLength": 1,
                                                                "type": "string"
                                                            },
                                                            "comments": {
                                                                "type": "string"
                                                            },
                                                            "legacy_subtitle_id": {
                                                                "type": "number"
                                                            },
                                                            "uploader": {
                                                                "required": [
                                                                    "name",
                                                                    "rank",
                                                                    "uploader_id"
                                                                ],
                                                                "type": "object",
                                                                "properties": {
                                                                    "uploader_id": {
                                                                        "type": "number"
                                                                    },
                                                                    "name": {
                                                                        "minLength": 1,
                                                                        "type": "string"
                                                                    },
                                                                    "rank": {
                                                                        "minLength": 1,
                                                                        "type": "string"
                                                                    }
                                                                }
                                                            },
                                                            "feature_details": {
                                                                "required": [
                                                                    "feature_id",
                                                                    "feature_type",
                                                                    "imdb_id",
                                                                    "movie_name",
                                                                    "title",
                                                                    "year"
                                                                ],
                                                                "type": "object",
                                                                "properties": {
                                                                    "feature_id": {
                                                                        "type": "number"
                                                                    },
                                                                    "feature_type": {
                                                                        "minLength": 1,
                                                                        "type": "string"
                                                                    },
                                                                    "year": {
                                                                        "type": "number"
                                                                    },
                                                                    "title": {
                                                                        "minLength": 1,
                                                                        "type": "string"
                                                                    },
                                                                    "movie_name": {
                                                                        "minLength": 1,
                                                                        "type": "string"
                                                                    },
                                                                    "imdb_id": {
                                                                        "type": "number"
                                                                    },
                                                                    "tmdb_id": {
                                                                        "type": "object"
                                                                    }
                                                                }
                                                            },
                                                            "url": {
                                                                "minLength": 1,
                                                                "type": "string"
                                                            },
                                                            "related_links": {
                                                                "required": [
                                                                    "img_url",
                                                                    "label",
                                                                    "url"
                                                                ],
                                                                "type": "object",
                                                                "properties": {
                                                                    "label": {
                                                                        "minLength": 1,
                                                                        "type": "string"
                                                                    },
                                                                    "url": {
                                                                        "minLength": 1,
                                                                        "type": "string"
                                                                    },
                                                                    "img_url": {
                                                                        "minLength": 1,
                                                                        "type": "string"
                                                                    }
                                                                }
                                                            },
                                                            "files": {
                                                                "minItems": 1,
                                                                "uniqueItems": true,
                                                                "type": "array",
                                                                "items": {
                                                                    "required": [
                                                                        "cd_number",
                                                                        "file_id",
                                                                        "file_name"
                                                                    ],
                                                                    "type": "object",
                                                                    "properties": {
                                                                        "file_id": {
                                                                            "type": "number"
                                                                        },
                                                                        "cd_number": {
                                                                            "type": "number"
                                                                        },
                                                                        "file_name": {
                                                                            "minLength": 1,
                                                                            "type": "string"
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    "description": ""
                                },
                                "examples": {
                                    "example": {
                                        "value": {
                                            "total_pages": 1,
                                            "total_count": 10,
                                            "page": 1,
                                            "data": [
                                                {
                                                    "id": "string",
                                                    "type": "string",
                                                    "attributes": {
                                                        "subtitle_id": "string",
                                                        "language": "string",
                                                        "download_count": 0,
                                                        "new_download_count": 0,
                                                        "hearing_impaired": true,
                                                        "hd": true,
                                                        "format": {},
                                                        "fps": 0,
                                                        "votes": 0,
                                                        "points": 0,
                                                        "ratings": 0,
                                                        "from_trusted": true,
                                                        "foreign_parts_only": true,
                                                        "ai_translated": true,
                                                        "machine_translated": {},
                                                        "upload_date": "string",
                                                        "release": "string",
                                                        "comments": "string",
                                                        "legacy_subtitle_id": 0,
                                                        "uploader": {
                                                            "uploader_id": 0,
                                                            "name": "string",
                                                            "rank": "string"
                                                        },
                                                        "feature_details": {
                                                            "feature_id": 0,
                                                            "feature_type": "string",
                                                            "year": 0,
                                                            "title": "string",
                                                            "movie_name": "string",
                                                            "imdb_id": 0,
                                                            "tmdb_id": {}
                                                        },
                                                        "url": "string",
                                                        "related_links": {
                                                            "label": "string",
                                                            "url": "string",
                                                            "img_url": "string"
                                                        },
                                                        "files": [
                                                            {
                                                                "file_id": 0,
                                                                "cd_number": 0,
                                                                "file_name": "string"
                                                            }
                                                        ]
                                                    }
                                                }
                                            ]
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "security": [
                    {
                        "Api-Key": []
                    }
                ]
            }
        },
        "/discover/most_downloaded": {
            "get": {
                "tags": [
                    "Discover"
                ],
                "summary": "Most downloaded subtitles",
                "description": "Discover popular subtitles, according to last 30 days downloads on opensubtitles.com. This list can be filtered by language code or feature type (movie, episode)",
                "operationId": "most_downloaded",
                "parameters": [
                    {
                        "name": "language",
                        "in": "query",
                        "description": "Language code, 1 language per query, or \"all\"",
                        "schema": {
                            "type": "string"
                        }
                    },
                    {
                        "name": "type",
                        "in": "query",
                        "description": "Type (movie or tvshow)",
                        "schema": {
                            "type": "string"
                        }
                    },
                    {
                        "schema": {
                            "type": "string"
                        },
                        "in": "header",
                        "name": "User-Agent",
                        "description": "<<{{APP_NAME}} v{{APP_VERSION}}>>"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Lists most downloaded movie subtitles ",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "description": "",
                                    "properties": {
                                        "total_pages": {
                                            "type": "number"
                                        },
                                        "total_count": {
                                            "type": "number"
                                        },
                                        "page": {
                                            "type": "number"
                                        },
                                        "data": {
                                            "minItems": 1,
                                            "uniqueItems": true,
                                            "type": "array",
                                            "items": {
                                                "$ref": "#/components/schemas/Subtitle"
                                            }
                                        }
                                    },
                                    "required": [
                                        "total_pages",
                                        "total_count",
                                        "page",
                                        "data"
                                    ]
                                },
                                "example": {
                                    "total_pages": 1,
                                    "total_count": 46,
                                    "page": 1,
                                    "data": [
                                        {
                                            "id": "493023",
                                            "type": "subtitle",
                                            "attributes": {
                                                "subtitle_id": "493023",
                                                "language": "nl",
                                                "download_count": 3889,
                                                "new_download_count": 11,
                                                "hearing_impaired": false,
                                                "hd": false,
                                                "format": "srt",
                                                "fps": 29.97,
                                                "votes": 0,
                                                "points": 0,
                                                "ratings": 0,
                                                "from_trusted": false,
                                                "foreign_parts_only": false,
                                                "ai_translated": false,
                                                "machine_translated": false,
                                                "upload_date": "2010-11-15T14:55:39.000Z",
                                                "release": "Major League WS DVDRip",
                                                "comments": "",
                                                "legacy_subtitle_id": 3956266,
                                                "uploader": {
                                                    "uploader_id": 3282,
                                                    "name": "COF7CJpS",
                                                    "rank": "app developer"
                                                },
                                                "feature_details": {
                                                    "feature_id": 518105,
                                                    "feature_type": "Movie",
                                                    "year": 1989,
                                                    "title": "Major League",
                                                    "movie_name": "1989 - Major League",
                                                    "imdb_id": 97815,
                                                    "tmdb_id": 9942
                                                },
                                                "url": "https://www.opensubtitles.com/nl/subtitles/legacy/3956266",
                                                "related_links": [
                                                    {
                                                        "label": "All subtitles for Major League",
                                                        "url": "https://www.opensubtitles.com/nl/movies/1989-major-league",
                                                        "img_url": "https://s9.osdb.link/features/5/0/1/518105.jpg"
                                                    }
                                                ],
                                                "files": [
                                                    {
                                                        "file_id": 544077,
                                                        "cd_number": 1,
                                                        "file_name": "Major League WS DVDRip.srt"
                                                    }
                                                ]
                                            }
                                        },
                                        {
                                            "id": "496423",
                                            "type": "subtitle",
                                            "attributes": {
                                                "subtitle_id": "496423",
                                                "language": "es",
                                                "download_count": 674,
                                                "new_download_count": 5,
                                                "hearing_impaired": false,
                                                "hd": false,
                                                "format": "",
                                                "fps": 29.97,
                                                "votes": 0,
                                                "points": 0,
                                                "ratings": 0,
                                                "from_trusted": false,
                                                "foreign_parts_only": false,
                                                "ai_translated": false,
                                                "machine_translated": false,
                                                "upload_date": "2008-03-23T21:04:04.000Z",
                                                "release": "Le mépris",
                                                "comments": "",
                                                "legacy_subtitle_id": 3264195,
                                                "uploader": {
                                                    "uploader_id": 3282,
                                                    "name": "COF7CJpS",
                                                    "rank": "app developer"
                                                },
                                                "feature_details": {
                                                    "feature_id": 518020,
                                                    "feature_type": "Movie",
                                                    "year": 1963,
                                                    "title": "Contempt",
                                                    "movie_name": "1963 - Contempt",
                                                    "imdb_id": 57345,
                                                    "tmdb_id": 266
                                                },
                                                "url": "https://www.opensubtitles.com/es/subtitles/legacy/3264195",
                                                "related_links": [
                                                    {
                                                        "label": "All subtitles for Contempt",
                                                        "url": "https://www.opensubtitles.com/es/movies/1963-contempt",
                                                        "img_url": "https://s9.osdb.link/features/0/2/0/518020.jpg"
                                                    }
                                                ],
                                                "files": [
                                                    {
                                                        "file_id": 6028018,
                                                        "cd_number": 1,
                                                        "file_name": "Le mepris-es.srt"
                                                    }
                                                ]
                                            }
                                        },
                                        {
                                            "id": "495449",
                                            "type": "subtitle",
                                            "attributes": {
                                                "subtitle_id": "495449",
                                                "language": "pt-BR",
                                                "download_count": 189,
                                                "new_download_count": 1,
                                                "hearing_impaired": false,
                                                "hd": false,
                                                "format": "",
                                                "fps": 23.976,
                                                "votes": 0,
                                                "points": 0,
                                                "ratings": 0,
                                                "from_trusted": false,
                                                "foreign_parts_only": false,
                                                "ai_translated": false,
                                                "machine_translated": false,
                                                "upload_date": "2012-07-14T19:47:18.000Z",
                                                "release": "Gnger Snaps",
                                                "comments": "",
                                                "legacy_subtitle_id": 4617243,
                                                "uploader": {
                                                    "uploader_id": 3282,
                                                    "name": "COF7CJpS",
                                                    "rank": "app developer"
                                                },
                                                "feature_details": {
                                                    "feature_id": 518342,
                                                    "feature_type": "Movie",
                                                    "year": 2000,
                                                    "title": "Ginger Snaps",
                                                    "movie_name": "2000 - Ginger Snaps",
                                                    "imdb_id": 210070,
                                                    "tmdb_id": 9871
                                                },
                                                "url": "https://www.opensubtitles.com/pt-BR/subtitles/legacy/4617243",
                                                "related_links": [
                                                    {
                                                        "label": "All subtitles for Ginger Snaps",
                                                        "url": "https://www.opensubtitles.com/pt-BR/movies/2000-ginger-snaps",
                                                        "img_url": "https://s9.osdb.link/features/2/4/3/518342.jpg"
                                                    }
                                                ],
                                                "files": [
                                                    {
                                                        "file_id": 546827,
                                                        "cd_number": 1,
                                                        "file_name": "Ginger Snaps [2000] DvDrip [Eng] Bugz.srt"
                                                    }
                                                ]
                                            }
                                        },
                                        {
                                            "id": "496964",
                                            "type": "subtitle",
                                            "attributes": {
                                                "subtitle_id": "496964",
                                                "language": "es",
                                                "download_count": 1190,
                                                "new_download_count": 7,
                                                "hearing_impaired": false,
                                                "hd": false,
                                                "format": "",
                                                "fps": 23.976,
                                                "votes": 1,
                                                "points": 10,
                                                "ratings": 10,
                                                "from_trusted": false,
                                                "foreign_parts_only": false,
                                                "ai_translated": false,
                                                "machine_translated": false,
                                                "upload_date": "2012-05-18T00:13:46.000Z",
                                                "release": "1963.El desprecio (subt)",
                                                "comments": "",
                                                "legacy_subtitle_id": 4552383,
                                                "uploader": {
                                                    "uploader_id": 63170,
                                                    "name": "robot2xl",
                                                    "rank": "read only"
                                                },
                                                "feature_details": {
                                                    "feature_id": 518020,
                                                    "feature_type": "Movie",
                                                    "year": 1963,
                                                    "title": "Contempt",
                                                    "movie_name": "1963 - Contempt",
                                                    "imdb_id": 57345,
                                                    "tmdb_id": 266
                                                },
                                                "url": "https://www.opensubtitles.com/es/subtitles/legacy/4552383",
                                                "related_links": [
                                                    {
                                                        "label": "All subtitles for Contempt",
                                                        "url": "https://www.opensubtitles.com/es/movies/1963-contempt",
                                                        "img_url": "https://s9.osdb.link/features/0/2/0/518020.jpg"
                                                    }
                                                ],
                                                "files": [
                                                    {
                                                        "file_id": 548446,
                                                        "cd_number": 1,
                                                        "file_name": "1963.El desprecio (subt).srt"
                                                    }
                                                ]
                                            }
                                        },
                                        {
                                            "id": "492641",
                                            "type": "subtitle",
                                            "attributes": {
                                                "subtitle_id": "492641",
                                                "language": "es",
                                                "download_count": 1477,
                                                "new_download_count": 2,
                                                "hearing_impaired": false,
                                                "hd": false,
                                                "format": "",
                                                "fps": 0,
                                                "votes": 0,
                                                "points": 0,
                                                "ratings": 0,
                                                "from_trusted": false,
                                                "foreign_parts_only": false,
                                                "ai_translated": false,
                                                "machine_translated": false,
                                                "upload_date": "2005-08-19T22:00:00.000Z",
                                                "release": "Philadelphia Story, The (1940)",
                                                "comments": "",
                                                "legacy_subtitle_id": 101000,
                                                "uploader": {
                                                    "uploader_id": 14715,
                                                    "name": "marlowe62 (a)",
                                                    "rank": "bronze member"
                                                },
                                                "feature_details": {
                                                    "feature_id": 518136,
                                                    "feature_type": "Movie",
                                                    "year": 1940,
                                                    "title": "The Philadelphia Story",
                                                    "movie_name": "1940 - The Philadelphia Story",
                                                    "imdb_id": 32904,
                                                    "tmdb_id": 981
                                                },
                                                "url": "https://www.opensubtitles.com/es/subtitles/legacy/101000",
                                                "related_links": [
                                                    {
                                                        "label": "All subtitles for The Philadelphia Story",
                                                        "url": "https://www.opensubtitles.com/es/movies/1940-the-philadelphia-story",
                                                        "img_url": "https://s9.osdb.link/features/6/3/1/518136.jpg"
                                                    }
                                                ],
                                                "files": [
                                                    {
                                                        "file_id": 6026506,
                                                        "cd_number": 1,
                                                        "file_name": "George Cukor - Historias de Filadelfia (1940) DvdRip XviD Mp3 Dual Divxclasico.Esp.srt"
                                                    }
                                                ]
                                            }
                                        },
                                        {
                                            "id": "493247",
                                            "type": "subtitle",
                                            "attributes": {
                                                "subtitle_id": "493247",
                                                "language": "el",
                                                "download_count": 1052,
                                                "new_download_count": 16,
                                                "hearing_impaired": false,
                                                "hd": true,
                                                "format": "",
                                                "fps": 23.976,
                                                "votes": 0,
                                                "points": 0,
                                                "ratings": 0,
                                                "from_trusted": false,
                                                "foreign_parts_only": false,
                                                "ai_translated": false,
                                                "machine_translated": false,
                                                "upload_date": "2011-05-17T07:28:54.000Z",
                                                "release": "Superman.1978.720.BluRay.x264-VarK",
                                                "comments": "",
                                                "legacy_subtitle_id": 4179141,
                                                "uploader": {
                                                    "uploader_id": 3282,
                                                    "name": "COF7CJpS",
                                                    "rank": "app developer"
                                                },
                                                "feature_details": {
                                                    "feature_id": 517956,
                                                    "feature_type": "Movie",
                                                    "year": 1978,
                                                    "title": "Superman",
                                                    "movie_name": "1978 - Superman",
                                                    "imdb_id": 78346,
                                                    "tmdb_id": 1924
                                                },
                                                "url": "https://www.opensubtitles.com/el/subtitles/legacy/4179141",
                                                "related_links": [
                                                    {
                                                        "label": "All subtitles for Superman",
                                                        "url": "https://www.opensubtitles.com/el/movies/1978-superman",
                                                        "img_url": "https://s9.osdb.link/features/6/5/9/517956.jpg"
                                                    }
                                                ],
                                                "files": [
                                                    {
                                                        "file_id": 544327,
                                                        "cd_number": 1,
                                                        "file_name": "Superman.1978.720.BluRay.x264-VarK.srt"
                                                    }
                                                ]
                                            }
                                        },
                                        {
                                            "id": "496017",
                                            "type": "subtitle",
                                            "attributes": {
                                                "subtitle_id": "496017",
                                                "language": "en",
                                                "download_count": 24642,
                                                "new_download_count": 8,
                                                "hearing_impaired": false,
                                                "hd": false,
                                                "format": "",
                                                "fps": 23.98,
                                                "votes": 13,
                                                "points": 81,
                                                "ratings": 6.2,
                                                "from_trusted": false,
                                                "foreign_parts_only": false,
                                                "ai_translated": false,
                                                "machine_translated": false,
                                                "upload_date": "2002-10-10T22:00:00.000Z",
                                                "release": "Jingle All the Way (1996)",
                                                "comments": "none",
                                                "legacy_subtitle_id": 32268,
                                                "uploader": {
                                                    "uploader_id": 6872,
                                                    "name": "alxmota (a)",
                                                    "rank": "bronze member"
                                                },
                                                "feature_details": {
                                                    "feature_id": 518213,
                                                    "feature_type": "Movie",
                                                    "year": 1996,
                                                    "title": "Jingle All the Way",
                                                    "movie_name": "1996 - Jingle All the Way",
                                                    "imdb_id": 116705,
                                                    "tmdb_id": 9279
                                                },
                                                "url": "https://www.opensubtitles.com/en/subtitles/legacy/32268",
                                                "related_links": [
                                                    {
                                                        "label": "All subtitles for Jingle All the Way",
                                                        "url": "https://www.opensubtitles.com/en/movies/1996-jingle-all-the-way",
                                                        "img_url": "https://s9.osdb.link/features/3/1/2/518213.jpg"
                                                    }
                                                ],
                                                "files": [
                                                    {
                                                        "file_id": 547446,
                                                        "cd_number": 1,
                                                        "file_name": "ingles.srt"
                                                    }
                                                ]
                                            }
                                        },
                                        {
                                            "id": "496396",
                                            "type": "subtitle",
                                            "attributes": {
                                                "subtitle_id": "496396",
                                                "language": "nl",
                                                "download_count": 1993,
                                                "new_download_count": 16,
                                                "hearing_impaired": false,
                                                "hd": false,
                                                "format": "",
                                                "fps": 25,
                                                "votes": 1,
                                                "points": 7,
                                                "ratings": 7,
                                                "from_trusted": false,
                                                "foreign_parts_only": false,
                                                "ai_translated": false,
                                                "machine_translated": false,
                                                "upload_date": "2013-10-10T22:54:26.000Z",
                                                "release": "Come and See (Idi i smotri) (1985)",
                                                "comments": "",
                                                "legacy_subtitle_id": 5217608,
                                                "uploader": {
                                                    "uploader_id": 3282,
                                                    "name": "COF7CJpS",
                                                    "rank": "app developer"
                                                },
                                                "feature_details": {
                                                    "feature_id": 518417,
                                                    "feature_type": "Movie",
                                                    "year": 1985,
                                                    "title": "Come and See",
                                                    "movie_name": "1985 - Come and See",
                                                    "imdb_id": 91251,
                                                    "tmdb_id": 25237
                                                },
                                                "url": "https://www.opensubtitles.com/nl/subtitles/legacy/5217608",
                                                "related_links": [
                                                    {
                                                        "label": "All subtitles for Come and See",
                                                        "url": "https://www.opensubtitles.com/nl/movies/1985-come-and-see",
                                                        "img_url": "https://s9.osdb.link/features/7/1/4/518417.jpg"
                                                    }
                                                ],
                                                "files": [
                                                    {
                                                        "file_id": 547857,
                                                        "cd_number": 1,
                                                        "file_name": "Come and See (Idi i smotri) (1985)-dut(1).srt"
                                                    }
                                                ]
                                            }
                                        },
                                        {
                                            "id": "492427",
                                            "type": "subtitle",
                                            "attributes": {
                                                "subtitle_id": "492427",
                                                "language": "pt-BR",
                                                "download_count": 358,
                                                "new_download_count": 3,
                                                "hearing_impaired": false,
                                                "hd": true,
                                                "format": "",
                                                "fps": 23.98,
                                                "votes": 1,
                                                "points": 1,
                                                "ratings": 1,
                                                "from_trusted": false,
                                                "foreign_parts_only": false,
                                                "ai_translated": false,
                                                "machine_translated": false,
                                                "upload_date": "2015-12-26T15:19:56.000Z",
                                                "release": "Rambo.First.Blood.II.1985.Ultimate.Uncut.Remastered.Edition.1080p.BluRay.x264.AAC-ETRG",
                                                "comments": "PT-BR subtitle uploaded by saidleugim",
                                                "legacy_subtitle_id": 6437707,
                                                "uploader": {
                                                    "uploader_id": 71162,
                                                    "name": "saidleugim",
                                                    "rank": "bronze member"
                                                },
                                                "feature_details": {
                                                    "feature_id": 517867,
                                                    "feature_type": "Movie",
                                                    "year": 1985,
                                                    "title": "Rambo: First Blood Part II",
                                                    "movie_name": "1985 - Rambo: First Blood Part II",
                                                    "imdb_id": 89880,
                                                    "tmdb_id": 1369
                                                },
                                                "url": "https://www.opensubtitles.com/pt-BR/subtitles/legacy/6437707",
                                                "related_links": [
                                                    {
                                                        "label": "All subtitles for Rambo: First Blood Part II",
                                                        "url": "https://www.opensubtitles.com/pt-BR/movies/1985-rambo-first-blood-part-ii",
                                                        "img_url": "https://s9.osdb.link/features/7/6/8/517867.jpg"
                                                    }
                                                ],
                                                "files": [
                                                    {
                                                        "file_id": 6026410,
                                                        "cd_number": 1,
                                                        "file_name": "Rambo.First.Blood.II.1985.Ultimate.Uncut.Remastered.Edition.1080p.BluRay.x264.AAC-ETRG.srt"
                                                    }
                                                ]
                                            }
                                        },
                                        {
                                            "id": "493721",
                                            "type": "subtitle",
                                            "attributes": {
                                                "subtitle_id": "493721",
                                                "language": "en",
                                                "download_count": 16956,
                                                "new_download_count": 4,
                                                "hearing_impaired": false,
                                                "hd": false,
                                                "format": "",
                                                "fps": 25,
                                                "votes": 7,
                                                "points": 67,
                                                "ratings": 9.6,
                                                "from_trusted": false,
                                                "foreign_parts_only": false,
                                                "ai_translated": false,
                                                "machine_translated": false,
                                                "upload_date": "2007-05-16T09:07:38.000Z",
                                                "release": "Hannibal",
                                                "comments": "",
                                                "legacy_subtitle_id": 3123830,
                                                "uploader": {
                                                    "uploader_id": 34153,
                                                    "name": "arkymedes",
                                                    "rank": "bronze member"
                                                },
                                                "feature_details": {
                                                    "feature_id": 517991,
                                                    "feature_type": "Movie",
                                                    "year": 2001,
                                                    "title": "Hannibal",
                                                    "movie_name": "2001 - Hannibal",
                                                    "imdb_id": 212985,
                                                    "tmdb_id": 9740
                                                },
                                                "url": "https://www.opensubtitles.com/en/subtitles/legacy/3123830",
                                                "related_links": [
                                                    {
                                                        "label": "All subtitles for Hannibal",
                                                        "url": "https://www.opensubtitles.com/en/movies/2001-hannibal",
                                                        "img_url": "https://s9.osdb.link/features/1/9/9/517991.jpg"
                                                    }
                                                ],
                                                "files": [
                                                    {
                                                        "file_id": 544852,
                                                        "cd_number": 1,
                                                        "file_name": "Hannibal.en.srt"
                                                    }
                                                ]
                                            }
                                        },
                                        {
                                            "id": "496722",
                                            "type": "subtitle",
                                            "attributes": {
                                                "subtitle_id": "496722",
                                                "language": "es",
                                                "download_count": 544,
                                                "new_download_count": 21,
                                                "hearing_impaired": false,
                                                "hd": true,
                                                "format": "",
                                                "fps": 25,
                                                "votes": 0,
                                                "points": 0,
                                                "ratings": 0,
                                                "from_trusted": true,
                                                "foreign_parts_only": false,
                                                "ai_translated": false,
                                                "machine_translated": false,
                                                "upload_date": "2011-05-28T08:48:56.000Z",
                                                "release": "Le Mepris (1963) HDRip Dual XviD Ac3 by FitoCorleone",
                                                "comments": "El.Desprecio.(Le.Mepris).(1963).HDRip.Dual.(Spa.Fr.).(Xvid+2Ac3).(proteinicos.es)...FitoCorleone.avi [1.47 Gb]/ Corregidos por el GTC de DivXClasico para Proteinicos y DXC",
                                                "legacy_subtitle_id": 4184944,
                                                "uploader": {
                                                    "uploader_id": 32127,
                                                    "name": "marlowe62",
                                                    "rank": "trusted"
                                                },
                                                "feature_details": {
                                                    "feature_id": 518020,
                                                    "feature_type": "Movie",
                                                    "year": 1963,
                                                    "title": "Contempt",
                                                    "movie_name": "1963 - Contempt",
                                                    "imdb_id": 57345,
                                                    "tmdb_id": 266
                                                },
                                                "url": "https://www.opensubtitles.com/es/subtitles/legacy/4184944",
                                                "related_links": [
                                                    {
                                                        "label": "All subtitles for Contempt",
                                                        "url": "https://www.opensubtitles.com/es/movies/1963-contempt",
                                                        "img_url": "https://s9.osdb.link/features/0/2/0/518020.jpg"
                                                    }
                                                ],
                                                "files": [
                                                    {
                                                        "file_id": 548202,
                                                        "cd_number": 1,
                                                        "file_name": "Le Mepris (1963) HDRip Dual XviD Ac3 by FitoCorleone.Esp.srt"
                                                    }
                                                ]
                                            }
                                        },
                                        {
                                            "id": "492688",
                                            "type": "subtitle",
                                            "attributes": {
                                                "subtitle_id": "492688",
                                                "language": "en",
                                                "download_count": 72506,
                                                "new_download_count": 62,
                                                "hearing_impaired": true,
                                                "hd": false,
                                                "format": "",
                                                "fps": 25,
                                                "votes": 2,
                                                "points": 20,
                                                "ratings": 10,
                                                "from_trusted": false,
                                                "foreign_parts_only": false,
                                                "ai_translated": false,
                                                "machine_translated": false,
                                                "upload_date": "2008-07-09T13:19:22.000Z",
                                                "release": "Rocky.I[1976]DvDrip-aXXo",
                                                "comments": "Rocky-The.Complete.Saga[2007]DvDrip-aXXo",
                                                "legacy_subtitle_id": 3302711,
                                                "uploader": {
                                                    "uploader_id": 119465,
                                                    "name": "os_robot",
                                                    "rank": "bronze member"
                                                },
                                                "feature_details": {
                                                    "feature_id": 517932,
                                                    "feature_type": "Movie",
                                                    "year": 1976,
                                                    "title": "Rocky",
                                                    "movie_name": "1976 - Rocky",
                                                    "imdb_id": 75148,
                                                    "tmdb_id": 1366
                                                },
                                                "url": "https://www.opensubtitles.com/en/subtitles/legacy/3302711",
                                                "related_links": [
                                                    {
                                                        "label": "All subtitles for Rocky",
                                                        "url": "https://www.opensubtitles.com/en/movies/1976-rocky",
                                                        "img_url": "https://s9.osdb.link/features/2/3/9/517932.jpg"
                                                    }
                                                ],
                                                "files": [
                                                    {
                                                        "file_id": 543715,
                                                        "cd_number": 1,
                                                        "file_name": "Rocky.I[1976]DvDrip-aXXo.srt"
                                                    }
                                                ]
                                            }
                                        },
                                        {
                                            "id": "490625",
                                            "type": "subtitle",
                                            "attributes": {
                                                "subtitle_id": "490625",
                                                "language": "en",
                                                "download_count": 7989,
                                                "new_download_count": 20,
                                                "hearing_impaired": false,
                                                "hd": true,
                                                "format": "",
                                                "fps": 0,
                                                "votes": 0,
                                                "points": 0,
                                                "ratings": 0,
                                                "from_trusted": false,
                                                "foreign_parts_only": false,
                                                "ai_translated": false,
                                                "machine_translated": false,
                                                "upload_date": "2013-07-06T11:07:28.000Z",
                                                "release": "9.Songs.2004.720p.BluRay.x264.anoXmous",
                                                "comments": "",
                                                "legacy_subtitle_id": 5075303,
                                                "uploader": {
                                                    "uploader_id": 3282,
                                                    "name": "COF7CJpS",
                                                    "rank": "app developer"
                                                },
                                                "feature_details": {
                                                    "feature_id": 518052,
                                                    "feature_type": "Movie",
                                                    "year": 2004,
                                                    "title": "9 Songs",
                                                    "movie_name": "2004 - 9 Songs",
                                                    "imdb_id": 411705,
                                                    "tmdb_id": 27
                                                },
                                                "url": "https://www.opensubtitles.com/en/subtitles/legacy/5075303",
                                                "related_links": [
                                                    {
                                                        "label": "All subtitles for 9 Songs",
                                                        "url": "https://www.opensubtitles.com/en/movies/2004-9-songs",
                                                        "img_url": "https://s9.osdb.link/features/2/5/0/518052.jpg"
                                                    }
                                                ],
                                                "files": [
                                                    {
                                                        "file_id": 541296,
                                                        "cd_number": 1,
                                                        "file_name": "9.Songs.2004.720p.BluRay.x264.anoXmous_eng.srt"
                                                    }
                                                ]
                                            }
                                        },
                                        {
                                            "id": "494835",
                                            "type": "subtitle",
                                            "attributes": {
                                                "subtitle_id": "494835",
                                                "language": "pt-BR",
                                                "download_count": 2028,
                                                "new_download_count": 10,
                                                "hearing_impaired": false,
                                                "hd": true,
                                                "format": "",
                                                "fps": 24,
                                                "votes": 2,
                                                "points": 20,
                                                "ratings": 10,
                                                "from_trusted": false,
                                                "foreign_parts_only": false,
                                                "ai_translated": false,
                                                "machine_translated": false,
                                                "upload_date": "2014-09-07T13:57:21.000Z",
                                                "release": "Red Sonja.1985.BDRip.720p.MultiLang.MultiSub-Pitt",
                                                "comments": "",
                                                "legacy_subtitle_id": 5815278,
                                                "uploader": {
                                                    "uploader_id": 62530,
                                                    "name": "fjones1979",
                                                    "rank": "trusted"
                                                },
                                                "feature_details": {
                                                    "feature_id": 518067,
                                                    "feature_type": "Movie",
                                                    "year": 1985,
                                                    "title": "Red Sonja",
                                                    "movie_name": "1985 - Red Sonja",
                                                    "imdb_id": 89893,
                                                    "tmdb_id": 9626
                                                },
                                                "url": "https://www.opensubtitles.com/pt-BR/subtitles/legacy/5815278",
                                                "related_links": [
                                                    {
                                                        "label": "All subtitles for Red Sonja",
                                                        "url": "https://www.opensubtitles.com/pt-BR/movies/1985-red-sonja",
                                                        "img_url": "https://s9.osdb.link/features/7/6/0/518067.jpg"
                                                    }
                                                ],
                                                "files": [
                                                    {
                                                        "file_id": 546129,
                                                        "cd_number": 1,
                                                        "file_name": "Red Sonja.1985.BDRip.720p.MultiLang.MultiSub-Pitt.por.srt"
                                                    }
                                                ]
                                            }
                                        },
                                        {
                                            "id": "492618",
                                            "type": "subtitle",
                                            "attributes": {
                                                "subtitle_id": "492618",
                                                "language": "pl",
                                                "download_count": 147,
                                                "new_download_count": 4,
                                                "hearing_impaired": false,
                                                "hd": true,
                                                "format": "",
                                                "fps": 0,
                                                "votes": 0,
                                                "points": 0,
                                                "ratings": 0,
                                                "from_trusted": false,
                                                "foreign_parts_only": false,
                                                "ai_translated": false,
                                                "machine_translated": false,
                                                "upload_date": "2015-07-08T20:47:42.000Z",
                                                "release": "Presumed.Innocent.1990.720p.BRRip.XviD.AC3-RARBG",
                                                "comments": "",
                                                "legacy_subtitle_id": 6228423,
                                                "uploader": {
                                                    "uploader_id": 3282,
                                                    "name": "COF7CJpS",
                                                    "rank": "app developer"
                                                },
                                                "feature_details": {
                                                    "feature_id": 517957,
                                                    "feature_type": "Movie",
                                                    "year": 1990,
                                                    "title": "Presumed Innocent",
                                                    "movie_name": "1990 - Presumed Innocent",
                                                    "imdb_id": 100404,
                                                    "tmdb_id": 11092
                                                },
                                                "url": "https://www.opensubtitles.com/pl/subtitles/legacy/6228423",
                                                "related_links": [
                                                    {
                                                        "label": "All subtitles for Presumed Innocent",
                                                        "url": "https://www.opensubtitles.com/pl/movies/1990-presumed-innocent",
                                                        "img_url": "https://s9.osdb.link/features/7/5/9/517957.jpg"
                                                    }
                                                ],
                                                "files": [
                                                    {
                                                        "file_id": 6026497,
                                                        "cd_number": 1,
                                                        "file_name": "Presumed.Innocent.1990.720p.BRRip.XviD.AC3-RARBG.txt"
                                                    }
                                                ]
                                            }
                                        },
                                        {
                                            "id": "496727",
                                            "type": "subtitle",
                                            "attributes": {
                                                "subtitle_id": "496727",
                                                "language": "en",
                                                "download_count": 1912,
                                                "new_download_count": 63,
                                                "hearing_impaired": false,
                                                "hd": true,
                                                "format": "",
                                                "fps": 23.976,
                                                "votes": 0,
                                                "points": 0,
                                                "ratings": 0,
                                                "from_trusted": false,
                                                "foreign_parts_only": false,
                                                "ai_translated": false,
                                                "machine_translated": false,
                                                "upload_date": "2016-08-12T06:53:45.000Z",
                                                "release": "Idi.i.smotri.AKA.Come.and.See.1985.IVC.1080p.BluRay.Remux.AVC.FLAC.2.0-oddset",
                                                "comments": "",
                                                "legacy_subtitle_id": 6708061,
                                                "uploader": {
                                                    "uploader_id": 3282,
                                                    "name": "COF7CJpS",
                                                    "rank": "app developer"
                                                },
                                                "feature_details": {
                                                    "feature_id": 518417,
                                                    "feature_type": "Movie",
                                                    "year": 1985,
                                                    "title": "Come and See",
                                                    "movie_name": "1985 - Come and See",
                                                    "imdb_id": 91251,
                                                    "tmdb_id": 25237
                                                },
                                                "url": "https://www.opensubtitles.com/en/subtitles/legacy/6708061",
                                                "related_links": [
                                                    {
                                                        "label": "All subtitles for Come and See",
                                                        "url": "https://www.opensubtitles.com/en/movies/1985-come-and-see",
                                                        "img_url": "https://s9.osdb.link/features/7/1/4/518417.jpg"
                                                    }
                                                ],
                                                "files": [
                                                    {
                                                        "file_id": 6028156,
                                                        "cd_number": 1,
                                                        "file_name": "Idi.i.smotri.AKA.Come.and.See.1985.IVC.1080p.BluRay.Remux.AVC.FLAC.2.0-oddset.srt"
                                                    }
                                                ]
                                            }
                                        },
                                        {
                                            "id": "493563",
                                            "type": "subtitle",
                                            "attributes": {
                                                "subtitle_id": "493563",
                                                "language": "en",
                                                "download_count": 14796,
                                                "new_download_count": 12,
                                                "hearing_impaired": false,
                                                "hd": false,
                                                "format": "",
                                                "fps": 23.976,
                                                "votes": 1,
                                                "points": 10,
                                                "ratings": 10,
                                                "from_trusted": false,
                                                "foreign_parts_only": false,
                                                "ai_translated": false,
                                                "machine_translated": false,
                                                "upload_date": "2001-12-04T23:00:00.000Z",
                                                "release": "The Secret Garden",
                                                "comments": "",
                                                "legacy_subtitle_id": 106540,
                                                "uploader": {
                                                    "uploader_id": 4143,
                                                    "name": "Panayot (a)",
                                                    "rank": "bronze member"
                                                },
                                                "feature_details": {
                                                    "feature_id": 518028,
                                                    "feature_type": "Movie",
                                                    "year": 1993,
                                                    "title": "The Secret Garden",
                                                    "movie_name": "1993 - The Secret Garden",
                                                    "imdb_id": 108071,
                                                    "tmdb_id": 11236
                                                },
                                                "url": "https://www.opensubtitles.com/en/subtitles/legacy/106540",
                                                "related_links": [
                                                    {
                                                        "label": "All subtitles for The Secret Garden",
                                                        "url": "https://www.opensubtitles.com/en/movies/1993-the-secret-garden",
                                                        "img_url": "https://s9.osdb.link/features/8/2/0/518028.jpg"
                                                    }
                                                ],
                                                "files": [
                                                    {
                                                        "file_id": 544691,
                                                        "cd_number": 1,
                                                        "file_name": "TheSecretGarden_EN.sub"
                                                    }
                                                ]
                                            }
                                        },
                                        {
                                            "id": "492466",
                                            "type": "subtitle",
                                            "attributes": {
                                                "subtitle_id": "492466",
                                                "language": "he",
                                                "download_count": 128,
                                                "new_download_count": 1,
                                                "hearing_impaired": false,
                                                "hd": false,
                                                "format": "",
                                                "fps": 0,
                                                "votes": 0,
                                                "points": 0,
                                                "ratings": 0,
                                                "from_trusted": false,
                                                "foreign_parts_only": false,
                                                "ai_translated": false,
                                                "machine_translated": false,
                                                "upload_date": "2008-02-08T02:00:42.000Z",
                                                "release": "Rocky.1976.DVDRip.XviD.AC3.iNTERNAL-QiM",
                                                "comments": "",
                                                "legacy_subtitle_id": 3246129,
                                                "uploader": {
                                                    "uploader_id": 3282,
                                                    "name": "COF7CJpS",
                                                    "rank": "app developer"
                                                },
                                                "feature_details": {
                                                    "feature_id": 517932,
                                                    "feature_type": "Movie",
                                                    "year": 1976,
                                                    "title": "Rocky",
                                                    "movie_name": "1976 - Rocky",
                                                    "imdb_id": 75148,
                                                    "tmdb_id": 1366
                                                },
                                                "url": "https://www.opensubtitles.com/he/subtitles/legacy/3246129",
                                                "related_links": [
                                                    {
                                                        "label": "All subtitles for Rocky",
                                                        "url": "https://www.opensubtitles.com/he/movies/1976-rocky",
                                                        "img_url": "https://s9.osdb.link/features/2/3/9/517932.jpg"
                                                    }
                                                ],
                                                "files": [
                                                    {
                                                        "file_id": 6026439,
                                                        "cd_number": 2,
                                                        "file_name": "qim-rockyb.srt"
                                                    },
                                                    {
                                                        "file_id": 6026437,
                                                        "cd_number": 1,
                                                        "file_name": "qim-rockya.srt"
                                                    }
                                                ]
                                            }
                                        },
                                        {
                                            "id": "492560",
                                            "type": "subtitle",
                                            "attributes": {
                                                "subtitle_id": "492560",
                                                "language": "pt-BR",
                                                "download_count": 64,
                                                "new_download_count": 2,
                                                "hearing_impaired": false,
                                                "hd": false,
                                                "format": "",
                                                "fps": 0,
                                                "votes": 0,
                                                "points": 0,
                                                "ratings": 0,
                                                "from_trusted": false,
                                                "foreign_parts_only": false,
                                                "ai_translated": false,
                                                "machine_translated": false,
                                                "upload_date": "2017-07-29T22:49:40.000Z",
                                                "release": "jornada",
                                                "comments": "",
                                                "legacy_subtitle_id": 7052825,
                                                "uploader": {
                                                    "uploader_id": 3282,
                                                    "name": "COF7CJpS",
                                                    "rank": "app developer"
                                                },
                                                "feature_details": {
                                                    "feature_id": 517867,
                                                    "feature_type": "Movie",
                                                    "year": 1985,
                                                    "title": "Rambo: First Blood Part II",
                                                    "movie_name": "1985 - Rambo: First Blood Part II",
                                                    "imdb_id": 89880,
                                                    "tmdb_id": 1369
                                                },
                                                "url": "https://www.opensubtitles.com/pt-BR/subtitles/legacy/7052825",
                                                "related_links": [
                                                    {
                                                        "label": "All subtitles for Rambo: First Blood Part II",
                                                        "url": "https://www.opensubtitles.com/pt-BR/movies/1985-rambo-first-blood-part-ii",
                                                        "img_url": "https://s9.osdb.link/features/7/6/8/517867.jpg"
                                                    }
                                                ],
                                                "files": [
                                                    {
                                                        "file_id": 6026472,
                                                        "cd_number": 1,
                                                        "file_name": "jornada.srt"
                                                    }
                                                ]
                                            }
                                        },
                                        {
                                            "id": "496159",
                                            "type": "subtitle",
                                            "attributes": {
                                                "subtitle_id": "496159",
                                                "language": "de",
                                                "download_count": 226,
                                                "new_download_count": 7,
                                                "hearing_impaired": false,
                                                "hd": false,
                                                "format": "",
                                                "fps": 25,
                                                "votes": 0,
                                                "points": 0,
                                                "ratings": 0,
                                                "from_trusted": true,
                                                "foreign_parts_only": false,
                                                "ai_translated": false,
                                                "machine_translated": false,
                                                "upload_date": "2012-07-21T17:11:45.000Z",
                                                "release": "Komm.und.sieh.1985.German.DVDRip.Retail",
                                                "comments": "RUSCICO / Russian Cinema Council",
                                                "legacy_subtitle_id": 4622375,
                                                "uploader": {
                                                    "uploader_id": 41812,
                                                    "name": "Ralle1",
                                                    "rank": "administrator"
                                                },
                                                "feature_details": {
                                                    "feature_id": 518417,
                                                    "feature_type": "Movie",
                                                    "year": 1985,
                                                    "title": "Come and See",
                                                    "movie_name": "1985 - Come and See",
                                                    "imdb_id": 91251,
                                                    "tmdb_id": 25237
                                                },
                                                "url": "https://www.opensubtitles.com/de/subtitles/legacy/4622375",
                                                "related_links": [
                                                    {
                                                        "label": "All subtitles for Come and See",
                                                        "url": "https://www.opensubtitles.com/de/movies/1985-come-and-see",
                                                        "img_url": "https://s9.osdb.link/features/7/1/4/518417.jpg"
                                                    }
                                                ],
                                                "files": [
                                                    {
                                                        "file_id": 6027938,
                                                        "cd_number": 2,
                                                        "file_name": "Komm.und.sieh.1985.German.DVDRip.CD2.Retail.srt"
                                                    },
                                                    {
                                                        "file_id": 6027936,
                                                        "cd_number": 1,
                                                        "file_name": "Komm.und.sieh.1985.German.DVDRip.CD1.Retail.srt"
                                                    }
                                                ]
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    }
                },
                "deprecated": false,
                "security": [
                    {
                        "Api-Key": []
                    }
                ]
            }
        },
        "/features": {
            "get": {
                "tags": [
                    "Features"
                ],
                "summary": "Search for features",
                "description": "With the \"query\" parameter, search for a Feature from a simple text input. Typically used for a text search or autocomplete.\n\nWith an ID, get basic information and subtitles count for a specific title.\n\nWith the \"query_match\" you can define the matched applied to the query: \n - \"start\" is the default behavior, it will query on the first letter entered to offer suggestions\n - \"word\" will return the match on the word, but not always matching the fulll title, for example searching \"roma\" will return \"holiday in roma\"\n - \"exact\" will exactly match the title, so here searching for \"roma\" will only return the movie(s) named \"roma\" \n\nWith the \"full_search\" you can extend the search to the translations of the title, so \"roma\" will also return \"rome\" \n\n<!-- theme: warning -->\n\n> ### Watch Out!\n>\n> If you create an autocomplete, don't set a too small refresh limit, remember you must not go over 40 requests per 10 seconds!",
                "operationId": "features",
                "parameters": [
                    {
                        "name": "query",
                        "in": "query",
                        "description": "query to search, release/file name accepted",
                        "schema": {
                            "minLength": 3,
                            "type": "string"
                        }
                    },
                    {
                        "name": "type",
                        "in": "query",
                        "description": "empty to list all or **movie**, **tvshow** or **episode**.",
                        "schema": {
                            "type": "string"
                        }
                    },
                    {
                        "name": "feature_id",
                        "in": "query",
                        "description": "opensubtitles **feature_id**",
                        "schema": {
                            "type": "integer"
                        }
                    },
                    {
                        "name": "imdb_id",
                        "in": "query",
                        "description": "IMDB ID, delete leading zeroes",
                        "schema": {
                            "type": "string"
                        }
                    },
                    {
                        "name": "tmdb_id",
                        "in": "query",
                        "description": "TheMovieDB ID - combine with type to avoid errors",
                        "schema": {
                            "type": "string"
                        }
                    },
                    {
                        "name": "year",
                        "in": "query",
                        "description": "Filter by year. Can only be used in combination with a query",
                        "schema": {
                            "type": "integer"
                        }
                    },
                    {
                        "schema": {
                            "type": "string"
                        },
                        "in": "header",
                        "name": "User-Agent",
                        "description": "<<{{APP_NAME}} v{{APP_VERSION}}>>"
                    },
                    {
                        "schema": {
                            "type": "string"
                        },
                        "in": "query",
                        "name": "query_match",
                        "description": "Type of matching applied to the query: **start** (default), **word**, **exact**  "
                    },
                    {
                        "schema": {
                            "type": "boolean"
                        },
                        "in": "query",
                        "name": "full_search",
                        "description": "Search on original title and title aka (translations) (default false)"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Search for a feature",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "movie": {
                                            "$ref": "#/components/schemas/Feature-Movie"
                                        },
                                        "episode": {
                                            "$ref": "#/components/schemas/Feature-Episode"
                                        },
                                        "tv": {
                                            "$ref": "#/components/schemas/Feature-Tvshow"
                                        }
                                    },
                                    "description": ""
                                },
                                "example": {
                                    "data": [
                                        {
                                            "id": "9803",
                                            "type": "feature",
                                            "attributes": {
                                                "title": "Waking the Dead",
                                                "original_title": "",
                                                "year": "2000",
                                                "subtitles_counts": {
                                                    "en": 68,
                                                    "es": 41,
                                                    "nl": 40,
                                                    "ro": 40,
                                                    "ru": 30,
                                                    "sr": 21,
                                                    "pl": 7,
                                                    "pt-BR": 4,
                                                    "hr": 3,
                                                    "pt-PT": 3,
                                                    "bg": 2,
                                                    "el": 2,
                                                    "he": 2,
                                                    "fa": 2,
                                                    "sl": 2,
                                                    "tr": 2,
                                                    "ar": 1,
                                                    "bs": 1,
                                                    "cs": 1,
                                                    "et": 1,
                                                    "fi": 1,
                                                    "fr": 1,
                                                    "hu": 1,
                                                    "id": 1,
                                                    "ja": 1,
                                                    "sk": 1,
                                                    "th": 1,
                                                    "vi": 1
                                                },
                                                "subtitles_count": 11,
                                                "seasons_count": 9,
                                                "parent_title": "",
                                                "season_number": 0,
                                                "episode_number": "",
                                                "imdb_id": 259733,
                                                "tmdb_id": 4860,
                                                "parent_imdb_id": "",
                                                "feature_id": "9803",
                                                "title_aka": [
                                                    "Waking the Dead",
                                                    " Waking the Dead – Im Auftrag der Toten"
                                                ],
                                                "feature_type": "Tvshow",
                                                "url": "https://www.opensubtitles.com/en/tvshows/2000-waking-the-dead",
                                                "img_url": "https://s9.osdb.link/features/3/0/8/9803.jpg",
                                                "seasons": [
                                                    {
                                                        "season_number": 1,
                                                        "episodes": [
                                                            {
                                                                "episode_number": 1,
                                                                "title": "\"Waking the Dead\" Pilot: Part 1",
                                                                "feature_id": 126854,
                                                                "feature_imdb_id": 743365
                                                            },
                                                            {
                                                                "episode_number": 2,
                                                                "title": "\"Waking the Dead\" Pilot: Part 2",
                                                                "feature_id": 126863,
                                                                "feature_imdb_id": 936019
                                                            },
                                                            {
                                                                "episode_number": 3,
                                                                "title": "\"Waking the Dead\" Burn Out: Part 1",
                                                                "feature_id": 126861,
                                                                "feature_imdb_id": 743355
                                                            },
                                                            {
                                                                "episode_number": 4,
                                                                "title": "\"Waking the Dead\" Burn Out: Part 2",
                                                                "feature_id": 126858,
                                                                "feature_imdb_id": 936016
                                                            },
                                                            {
                                                                "episode_number": 5,
                                                                "title": "\"Waking the Dead\" Blind Beggar: Part 1",
                                                                "feature_id": 126862,
                                                                "feature_imdb_id": 743353
                                                            },
                                                            {
                                                                "episode_number": 6,
                                                                "title": "\"Waking the Dead\" Blind Beggar: Part 2",
                                                                "feature_id": 126859,
                                                                "feature_imdb_id": 936017
                                                            },
                                                            {
                                                                "episode_number": 7,
                                                                "title": "\"Waking the Dead\" A Simple Sacrifice: Part 1",
                                                                "feature_id": 126860,
                                                                "feature_imdb_id": 743350
                                                            },
                                                            {
                                                                "episode_number": 8,
                                                                "title": "\"Waking the Dead\" A Simple Sacrifice: Part 2",
                                                                "feature_id": 126864,
                                                                "feature_imdb_id": 936015
                                                            },
                                                            {
                                                                "episode_number": 9,
                                                                "title": "\"Waking the Dead\" Every Breath You Take: Part 1",
                                                                "feature_id": 126865,
                                                                "feature_imdb_id": 743358
                                                            },
                                                            {
                                                                "episode_number": 10,
                                                                "title": "\"Waking the Dead\" Every Breath You Take: Part 2",
                                                                "feature_id": 126869,
                                                                "feature_imdb_id": 936018
                                                            }
                                                        ]
                                                    },
                                                    {
                                                        "season_number": 2,
                                                        "episodes": [
                                                            {
                                                                "episode_number": 1,
                                                                "title": "\"Waking the Dead\" Life Sentence: Part 1",
                                                                "feature_id": 126868,
                                                                "feature_imdb_id": 743363
                                                            },
                                                            {
                                                                "episode_number": 2,
                                                                "title": "\"Waking the Dead\" Life Sentence: Part 2",
                                                                "feature_id": 126871,
                                                                "feature_imdb_id": 1108804
                                                            },
                                                            {
                                                                "episode_number": 3,
                                                                "title": "\"Waking the Dead\" Deathwatch: Part 1",
                                                                "feature_id": 126867,
                                                                "feature_imdb_id": 743357
                                                            },
                                                            {
                                                                "episode_number": 4,
                                                                "title": "\"Waking the Dead\" Deathwatch: Part 2",
                                                                "feature_id": 126870,
                                                                "feature_imdb_id": 1108805
                                                            },
                                                            {
                                                                "episode_number": 5,
                                                                "title": "\"Waking the Dead\" Special Relationship: Part 1",
                                                                "feature_id": 126872,
                                                                "feature_imdb_id": 743367
                                                            },
                                                            {
                                                                "episode_number": 6,
                                                                "title": "\"Waking the Dead\" Special Relationship: Part 2",
                                                                "feature_id": 126878,
                                                                "feature_imdb_id": 1091606
                                                            },
                                                            {
                                                                "episode_number": 7,
                                                                "title": "\"Waking the Dead\" Thin Air: Part 1",
                                                                "feature_id": 126875,
                                                                "feature_imdb_id": 743371
                                                            },
                                                            {
                                                                "episode_number": 8,
                                                                "title": "\"Waking the Dead\" Thin Air: Part 2",
                                                                "feature_id": 126877,
                                                                "feature_imdb_id": 1167299
                                                            }
                                                        ]
                                                    },
                                                    {
                                                        "season_number": 3,
                                                        "episodes": [
                                                            {
                                                                "episode_number": 1,
                                                                "title": "\"Waking the Dead\" Multistorey: Part 1",
                                                                "feature_id": 126876,
                                                                "feature_imdb_id": 743364
                                                            },
                                                            {
                                                                "episode_number": 2,
                                                                "title": "\"Waking the Dead\" Multistorey: Part 2",
                                                                "feature_id": 126883,
                                                                "feature_imdb_id": 1167294
                                                            },
                                                            {
                                                                "episode_number": 3,
                                                                "title": "\"Waking the Dead\" Walking on Water: Part 1",
                                                                "feature_id": 126884,
                                                                "feature_imdb_id": 743374
                                                            },
                                                            {
                                                                "episode_number": 4,
                                                                "title": "\"Waking the Dead\" Walking on Water: Part 2",
                                                                "feature_id": 126879,
                                                                "feature_imdb_id": 1167302
                                                            },
                                                            {
                                                                "episode_number": 5,
                                                                "title": "\"Waking the Dead\" Breaking Glass: Part 1",
                                                                "feature_id": 126885,
                                                                "feature_imdb_id": 743354
                                                            },
                                                            {
                                                                "episode_number": 6,
                                                                "title": "\"Waking the Dead\" Breaking Glass: Part 2",
                                                                "feature_id": 126881,
                                                                "feature_imdb_id": 1167289
                                                            },
                                                            {
                                                                "episode_number": 7,
                                                                "title": "\"Waking the Dead\" Final Cut: Part 1",
                                                                "feature_id": 126887,
                                                                "feature_imdb_id": 743360
                                                            },
                                                            {
                                                                "episode_number": 8,
                                                                "title": "\"Waking the Dead\" Final Cut: Part 2",
                                                                "feature_id": 126882,
                                                                "feature_imdb_id": 1167292
                                                            }
                                                        ]
                                                    },
                                                    {
                                                        "season_number": 4,
                                                        "episodes": [
                                                            {
                                                                "episode_number": 1,
                                                                "title": "\"Waking the Dead\" In Sight of the Lord: Part 1",
                                                                "feature_id": 126888,
                                                                "feature_imdb_id": 743362
                                                            },
                                                            {
                                                                "episode_number": 2,
                                                                "title": "\"Waking the Dead\" In Sight of the Lord: Part 2",
                                                                "feature_id": 126866,
                                                                "feature_imdb_id": 1103924
                                                            },
                                                            {
                                                                "episode_number": 3,
                                                                "title": "\"Waking the Dead\" False Flag: Part 1",
                                                                "feature_id": 126852,
                                                                "feature_imdb_id": 743359
                                                            },
                                                            {
                                                                "episode_number": 4,
                                                                "title": "\"Waking the Dead\" False Flag: Part 2",
                                                                "feature_id": 126857,
                                                                "feature_imdb_id": 1167291
                                                            },
                                                            {
                                                                "episode_number": 5,
                                                                "title": "\"Waking the Dead\" Fugue States: Part 1",
                                                                "feature_id": 126880,
                                                                "feature_imdb_id": 743361
                                                            },
                                                            {
                                                                "episode_number": 6,
                                                                "title": "\"Waking the Dead\" Fugue States: Part 2",
                                                                "feature_id": 126886,
                                                                "feature_imdb_id": 1167293
                                                            },
                                                            {
                                                                "episode_number": 7,
                                                                "title": "\"Waking the Dead\" Anger Management: Part 1",
                                                                "feature_id": 126889,
                                                                "feature_imdb_id": 743351
                                                            },
                                                            {
                                                                "episode_number": 8,
                                                                "title": "\"Waking the Dead\" Anger Management: Part 2",
                                                                "feature_id": 126874,
                                                                "feature_imdb_id": 1167287
                                                            },
                                                            {
                                                                "episode_number": 9,
                                                                "title": "\"Waking the Dead\" The Hardest Word: Part 1",
                                                                "feature_id": 126891,
                                                                "feature_imdb_id": 743370
                                                            },
                                                            {
                                                                "episode_number": 10,
                                                                "title": "\"Waking the Dead\" The Hardest Word: Part 2",
                                                                "feature_id": 126890,
                                                                "feature_imdb_id": 1167298
                                                            },
                                                            {
                                                                "episode_number": 11,
                                                                "title": "\"Waking the Dead\" Shadowplay: Part 1",
                                                                "feature_id": 126893,
                                                                "feature_imdb_id": 743366
                                                            },
                                                            {
                                                                "episode_number": 12,
                                                                "title": "\"Waking the Dead\" Shadowplay: Part 2",
                                                                "feature_id": 126892,
                                                                "feature_imdb_id": 1167295
                                                            }
                                                        ]
                                                    },
                                                    {
                                                        "season_number": 5,
                                                        "episodes": [
                                                            {
                                                                "episode_number": 1,
                                                                "title": "\"Waking the Dead\" Towers of Silence: Part 1",
                                                                "feature_id": 126810,
                                                                "feature_imdb_id": 743372
                                                            },
                                                            {
                                                                "episode_number": 2,
                                                                "title": "\"Waking the Dead\" Towers of Silence: Part 2",
                                                                "feature_id": 126811,
                                                                "feature_imdb_id": 1167300
                                                            },
                                                            {
                                                                "episode_number": 3,
                                                                "title": "\"Waking the Dead\" Black Run: Part 1",
                                                                "feature_id": 126814,
                                                                "feature_imdb_id": 743352
                                                            },
                                                            {
                                                                "episode_number": 4,
                                                                "title": "\"Waking the Dead\" Black Run: Part 2",
                                                                "feature_id": 126808,
                                                                "feature_imdb_id": 1167288
                                                            },
                                                            {
                                                                "episode_number": 5,
                                                                "title": "\"Waking the Dead\" Subterraneans: Part 1",
                                                                "feature_id": 126816,
                                                                "feature_imdb_id": 743369
                                                            },
                                                            {
                                                                "episode_number": 6,
                                                                "title": "\"Waking the Dead\" Subterraneans: Part 2",
                                                                "feature_id": 126818,
                                                                "feature_imdb_id": 1167297
                                                            },
                                                            {
                                                                "episode_number": 7,
                                                                "title": "\"Waking the Dead\" Straw Dog: Part 1",
                                                                "feature_id": 126820,
                                                                "feature_imdb_id": 743368
                                                            },
                                                            {
                                                                "episode_number": 8,
                                                                "title": "\"Waking the Dead\" Straw Dog: Part 2",
                                                                "feature_id": 126822,
                                                                "feature_imdb_id": 1167296
                                                            },
                                                            {
                                                                "episode_number": 9,
                                                                "title": "\"Waking the Dead\" Undertow: Part 1",
                                                                "feature_id": 126819,
                                                                "feature_imdb_id": 743373
                                                            },
                                                            {
                                                                "episode_number": 10,
                                                                "title": "\"Waking the Dead\" Undertow: Part 2",
                                                                "feature_id": 126821,
                                                                "feature_imdb_id": 1167301
                                                            },
                                                            {
                                                                "episode_number": 11,
                                                                "title": "\"Waking the Dead\" Cold Fusion: Part 1",
                                                                "feature_id": 126823,
                                                                "feature_imdb_id": 743356
                                                            },
                                                            {
                                                                "episode_number": 12,
                                                                "title": "\"Waking the Dead\" Cold Fusion: Part 2",
                                                                "feature_id": 126817,
                                                                "feature_imdb_id": 1167290
                                                            }
                                                        ]
                                                    },
                                                    {
                                                        "season_number": 6,
                                                        "episodes": [
                                                            {
                                                                "episode_number": 1,
                                                                "title": "\"Waking the Dead\" Wren Boys: Part 1",
                                                                "feature_id": 126895,
                                                                "feature_imdb_id": 930851
                                                            },
                                                            {
                                                                "episode_number": 2,
                                                                "title": "\"Waking the Dead\" Wren Boys: Part 2",
                                                                "feature_id": 126855,
                                                                "feature_imdb_id": 932475
                                                            },
                                                            {
                                                                "episode_number": 3,
                                                                "title": "\"Waking the Dead\" Deus Ex Machina: Part 1",
                                                                "feature_id": 126894,
                                                                "feature_imdb_id": 932472
                                                            },
                                                            {
                                                                "episode_number": 4,
                                                                "title": "\"Waking the Dead\" Deus Ex Machina: Part 2",
                                                                "feature_id": 126896,
                                                                "feature_imdb_id": 932473
                                                            },
                                                            {
                                                                "episode_number": 5,
                                                                "title": "\"Waking the Dead\" The Fall: Part 1",
                                                                "feature_id": 126898,
                                                                "feature_imdb_id": 875569
                                                            },
                                                            {
                                                                "episode_number": 6,
                                                                "title": "\"Waking the Dead\" The Fall: Part 2",
                                                                "feature_id": 126873,
                                                                "feature_imdb_id": 938259
                                                            },
                                                            {
                                                                "episode_number": 7,
                                                                "title": "\"Waking the Dead\" Mask of Sanity: Part 1",
                                                                "feature_id": 126899,
                                                                "feature_imdb_id": 952542
                                                            },
                                                            {
                                                                "episode_number": 8,
                                                                "title": "\"Waking the Dead\" Mask of Sanity: Part 2",
                                                                "feature_id": 126902,
                                                                "feature_imdb_id": 952543
                                                            },
                                                            {
                                                                "episode_number": 9,
                                                                "title": "\"Waking the Dead\" Double Bind: Part 1",
                                                                "feature_id": 126897,
                                                                "feature_imdb_id": 952540
                                                            },
                                                            {
                                                                "episode_number": 10,
                                                                "title": "\"Waking the Dead\" Double Bind: Part 2",
                                                                "feature_id": 126903,
                                                                "feature_imdb_id": 952541
                                                            },
                                                            {
                                                                "episode_number": 11,
                                                                "title": "\"Waking the Dead\" Yahrzeit: Part 1",
                                                                "feature_id": 126901,
                                                                "feature_imdb_id": 892727
                                                            },
                                                            {
                                                                "episode_number": 12,
                                                                "title": "\"Waking the Dead\" Yahrzeit: Part 2",
                                                                "feature_id": 126900,
                                                                "feature_imdb_id": 942279
                                                            }
                                                        ]
                                                    },
                                                    {
                                                        "season_number": 7,
                                                        "episodes": [
                                                            {
                                                                "episode_number": 1,
                                                                "title": "\"Waking the Dead\" Missing Persons: Part 1",
                                                                "feature_id": 126825,
                                                                "feature_imdb_id": 1215441
                                                            },
                                                            {
                                                                "episode_number": 2,
                                                                "title": "\"Waking the Dead\" Missing Persons: Part 2",
                                                                "feature_id": 126824,
                                                                "feature_imdb_id": 1215442
                                                            },
                                                            {
                                                                "episode_number": 3,
                                                                "title": "\"Waking the Dead\" Sins: Part 1",
                                                                "feature_id": 126815,
                                                                "feature_imdb_id": 1218284
                                                            },
                                                            {
                                                                "episode_number": 4,
                                                                "title": "\"Waking the Dead\" Sins: Part 2",
                                                                "feature_id": 126826,
                                                                "feature_imdb_id": 1218285
                                                            },
                                                            {
                                                                "episode_number": 5,
                                                                "title": "\"Waking the Dead\" Duty and Honour: Part 1",
                                                                "feature_id": 126828,
                                                                "feature_imdb_id": 1221781
                                                            },
                                                            {
                                                                "episode_number": 6,
                                                                "title": "\"Waking the Dead\" Duty and Honour: Part 2",
                                                                "feature_id": 126830,
                                                                "feature_imdb_id": 1221782
                                                            },
                                                            {
                                                                "episode_number": 7,
                                                                "title": "\"Waking the Dead\" Skin: Part 1",
                                                                "feature_id": 126829,
                                                                "feature_imdb_id": 1225236
                                                            },
                                                            {
                                                                "episode_number": 8,
                                                                "title": "\"Waking the Dead\" Skin: Part 2",
                                                                "feature_id": 126831,
                                                                "feature_imdb_id": 1225237
                                                            },
                                                            {
                                                                "episode_number": 9,
                                                                "title": "\"Waking the Dead\" Wounds: Part 1",
                                                                "feature_id": 126827,
                                                                "feature_imdb_id": 1227115
                                                            },
                                                            {
                                                                "episode_number": 10,
                                                                "title": "\"Waking the Dead\" Wounds: Part 2",
                                                                "feature_id": 126834,
                                                                "feature_imdb_id": 1227116
                                                            },
                                                            {
                                                                "episode_number": 11,
                                                                "title": "\"Waking the Dead\" Pieta: Part 1",
                                                                "feature_id": 126833,
                                                                "feature_imdb_id": 1231221
                                                            },
                                                            {
                                                                "episode_number": 12,
                                                                "title": "\"Waking the Dead\" Pietà: Part 2",
                                                                "feature_id": 126832,
                                                                "feature_imdb_id": 1231222
                                                            }
                                                        ]
                                                    },
                                                    {
                                                        "season_number": 8,
                                                        "episodes": [
                                                            {
                                                                "episode_number": 1,
                                                                "title": "\"Waking the Dead\" Magdalene 26: Part 1",
                                                                "feature_id": 126836,
                                                                "feature_imdb_id": 1506431
                                                            },
                                                            {
                                                                "episode_number": 2,
                                                                "title": "\"Waking the Dead\" Magdalene 26: Part 2",
                                                                "feature_id": 126839,
                                                                "feature_imdb_id": 1506432
                                                            },
                                                            {
                                                                "episode_number": 3,
                                                                "title": "\"Waking the Dead\" End of the Night: Part 1",
                                                                "feature_id": 126837,
                                                                "feature_imdb_id": 1509622
                                                            },
                                                            {
                                                                "episode_number": 4,
                                                                "title": "\"Waking the Dead\" End of the Night: Part 2",
                                                                "feature_id": 126838,
                                                                "feature_imdb_id": 1509623
                                                            },
                                                            {
                                                                "episode_number": 5,
                                                                "title": "\"Waking the Dead\" Substitute: Part 1",
                                                                "feature_id": 126840,
                                                                "feature_imdb_id": 1513669
                                                            },
                                                            {
                                                                "episode_number": 6,
                                                                "title": "\"Waking the Dead\" Substitute: Part 2",
                                                                "feature_id": 126842,
                                                                "feature_imdb_id": 1514406
                                                            },
                                                            {
                                                                "episode_number": 7,
                                                                "title": "\"Waking the Dead\" End Game: Part 1",
                                                                "feature_id": 126846,
                                                                "feature_imdb_id": 1519231
                                                            },
                                                            {
                                                                "episode_number": 8,
                                                                "title": "\"Waking the Dead\" End Game: Part 2",
                                                                "feature_id": 126843,
                                                                "feature_imdb_id": 1519232
                                                            }
                                                        ]
                                                    },
                                                    {
                                                        "season_number": 9,
                                                        "episodes": [
                                                            {
                                                                "episode_number": 1,
                                                                "title": "\"Waking the Dead\" Harbinger: Part 1",
                                                                "feature_id": 126856,
                                                                "feature_imdb_id": 1862440
                                                            },
                                                            {
                                                                "episode_number": 2,
                                                                "title": "\"Waking the Dead\" Harbinger: Part 2",
                                                                "feature_id": 126853,
                                                                "feature_imdb_id": 1862441
                                                            },
                                                            {
                                                                "episode_number": 3,
                                                                "title": "\"Waking the Dead\" Care: Part 1",
                                                                "feature_id": 126844,
                                                                "feature_imdb_id": 1865234
                                                            },
                                                            {
                                                                "episode_number": 4,
                                                                "title": "\"Waking the Dead\" Care: Part 2",
                                                                "feature_id": 126845,
                                                                "feature_imdb_id": 1865235
                                                            },
                                                            {
                                                                "episode_number": 5,
                                                                "title": "\"Waking the Dead\" Solidarity: Part 1",
                                                                "feature_id": 126849,
                                                                "feature_imdb_id": 1869183
                                                            },
                                                            {
                                                                "episode_number": 6,
                                                                "title": "\"Waking the Dead\" Solidarity: Part 2",
                                                                "feature_id": 126851,
                                                                "feature_imdb_id": 1869184
                                                            },
                                                            {
                                                                "episode_number": 7,
                                                                "title": "\"Waking the Dead\" Conviction: Part 1",
                                                                "feature_id": 126848,
                                                                "feature_imdb_id": 1877523
                                                            },
                                                            {
                                                                "episode_number": 8,
                                                                "title": "\"Waking the Dead\" Conviction: Part 2",
                                                                "feature_id": 126841,
                                                                "feature_imdb_id": 1877524
                                                            },
                                                            {
                                                                "episode_number": 9,
                                                                "title": "\"Waking the Dead\" Waterloo, Part 1",
                                                                "feature_id": 126850,
                                                                "feature_imdb_id": 1886367
                                                            },
                                                            {
                                                                "episode_number": 10,
                                                                "title": "\"Waking the Dead\" Waterloo, Part 2",
                                                                "feature_id": 126847,
                                                                "feature_imdb_id": 1886368
                                                            }
                                                        ]
                                                    }
                                                ]
                                            }
                                        },
                                        {
                                            "id": "126842",
                                            "type": "feature",
                                            "attributes": {
                                                "title": "\"Waking the Dead\" Substitute: Part 2",
                                                "original_title": "",
                                                "year": "2009",
                                                "subtitles_counts": {
                                                    "nl": 1,
                                                    "en": 1,
                                                    "sr": 1,
                                                    "es": 1
                                                },
                                                "subtitles_count": 4,
                                                "seasons_count": 0,
                                                "parent_title": "Waking the Dead",
                                                "season_number": 8,
                                                "episode_number": 6,
                                                "imdb_id": 1514406,
                                                "tmdb_id": "",
                                                "parent_imdb_id": 259733,
                                                "feature_id": "126842",
                                                "title_aka": [
                                                    "\"Waking the Dead\" Substitute: Part 2"
                                                ],
                                                "feature_type": "Episode",
                                                "url": "https://www.opensubtitles.com/en/tvshows/2000-waking-the-dead/seasons/8/episodes/6-waking-the-dead-substitute-part-2",
                                                "img_url": "https://s9.osdb.link/features/2/4/8/126842.jpg",
                                                "seasons": []
                                            }
                                        },
                                        {
                                            "id": "126810",
                                            "type": "feature",
                                            "attributes": {
                                                "title": "\"Waking the Dead\" Towers of Silence: Part 1",
                                                "original_title": "",
                                                "year": "2005",
                                                "subtitles_counts": {
                                                    "es": 10,
                                                    "en": 4,
                                                    "pl": 3,
                                                    "pt-PT": 3,
                                                    "bg": 2,
                                                    "he": 2,
                                                    "fa": 2,
                                                    "ru": 2,
                                                    "sr": 2,
                                                    "tr": 2,
                                                    "ro": 2,
                                                    "pt-BR": 2,
                                                    "ar": 1,
                                                    "bs": 1,
                                                    "cs": 1,
                                                    "nl": 1,
                                                    "et": 1,
                                                    "fi": 1,
                                                    "fr": 1,
                                                    "el": 1,
                                                    "hr": 1,
                                                    "hu": 1,
                                                    "id": 1,
                                                    "ja": 1,
                                                    "sk": 1,
                                                    "sl": 1,
                                                    "th": 1,
                                                    "vi": 1
                                                },
                                                "subtitles_count": 52,
                                                "seasons_count": 0,
                                                "parent_title": "Waking the Dead",
                                                "season_number": 5,
                                                "episode_number": 1,
                                                "imdb_id": 743372,
                                                "tmdb_id": "",
                                                "parent_imdb_id": 259733,
                                                "feature_id": "126810",
                                                "title_aka": [
                                                    "\"Waking the Dead\" Towers of Silence: Part 1"
                                                ],
                                                "feature_type": "Episode",
                                                "url": "https://www.opensubtitles.com/en/tvshows/2000-waking-the-dead/seasons/5/episodes/1-waking-the-dead-towers-of-silence-part-1",
                                                "img_url": "https://s9.osdb.link/features/0/1/8/126810.jpg",
                                                "seasons": []
                                            }
                                        },
                                        {
                                            "id": "646786",
                                            "type": "feature",
                                            "attributes": {
                                                "title": "Waking the Dead",
                                                "original_title": "Waking the Dead",
                                                "year": "2000",
                                                "subtitles_counts": {
                                                    "en": 68,
                                                    "es": 41,
                                                    "nl": 40,
                                                    "ro": 40,
                                                    "ru": 30,
                                                    "sr": 21,
                                                    "pl": 7,
                                                    "pt-BR": 4,
                                                    "hr": 3,
                                                    "pt-PT": 3,
                                                    "bg": 2,
                                                    "el": 2,
                                                    "he": 2,
                                                    "fa": 2,
                                                    "sl": 2,
                                                    "tr": 2,
                                                    "ar": 1,
                                                    "bs": 1,
                                                    "cs": 1,
                                                    "et": 1,
                                                    "fi": 1,
                                                    "fr": 1,
                                                    "hu": 1,
                                                    "id": 1,
                                                    "ja": 1,
                                                    "sk": 1,
                                                    "th": 1,
                                                    "vi": 1
                                                },
                                                "subtitles_count": 25,
                                                "seasons_count": 0,
                                                "parent_title": "",
                                                "season_number": 0,
                                                "episode_number": "",
                                                "imdb_id": 127349,
                                                "tmdb_id": 37722,
                                                "parent_imdb_id": "",
                                                "feature_id": "646786",
                                                "title_aka": [
                                                    "Waking the Dead",
                                                    " Resucitar un amor",
                                                    " Le Fantôme de Sarah Williams",
                                                    " Szerelmem szelleme",
                                                    " Amor Maior que a Vida",
                                                    " Пробуждая мертвецов",
                                                    " 死亡中惊醒"
                                                ],
                                                "feature_type": "Movie",
                                                "url": "https://www.opensubtitles.com/en/movies/2000-waking-the-dead-5559",
                                                "img_url": "https://s9.osdb.link/features/6/8/7/646786.jpg",
                                                "seasons": []
                                            }
                                        },
                                        {
                                            "id": "126847",
                                            "type": "feature",
                                            "attributes": {
                                                "title": "\"Waking the Dead\" Waterloo, Part 2",
                                                "original_title": "",
                                                "year": "2011",
                                                "subtitles_counts": {
                                                    "nl": 1,
                                                    "en": 1,
                                                    "sr": 1,
                                                    "ro": 1
                                                },
                                                "subtitles_count": 4,
                                                "seasons_count": 0,
                                                "parent_title": "Waking the Dead",
                                                "season_number": 9,
                                                "episode_number": 10,
                                                "imdb_id": 1886368,
                                                "tmdb_id": "",
                                                "parent_imdb_id": 259733,
                                                "feature_id": "126847",
                                                "title_aka": [
                                                    "\"Waking the Dead\" Waterloo",
                                                    " Part 2"
                                                ],
                                                "feature_type": "Episode",
                                                "url": "https://www.opensubtitles.com/en/tvshows/2000-waking-the-dead/seasons/9/episodes/10-waking-the-dead-waterloo-part-2",
                                                "img_url": "",
                                                "seasons": []
                                            }
                                        },
                                        {
                                            "id": "126857",
                                            "type": "feature",
                                            "attributes": {
                                                "title": "\"Waking the Dead\" False Flag: Part 2",
                                                "original_title": "",
                                                "year": "2004",
                                                "subtitles_counts": {
                                                    "ru": 2,
                                                    "ro": 2,
                                                    "en": 1
                                                },
                                                "subtitles_count": 5,
                                                "seasons_count": 0,
                                                "parent_title": "Waking the Dead",
                                                "season_number": 4,
                                                "episode_number": 4,
                                                "imdb_id": 1167291,
                                                "tmdb_id": "",
                                                "parent_imdb_id": 259733,
                                                "feature_id": "126857",
                                                "title_aka": [
                                                    "\"Waking the Dead\" False Flag: Part 2"
                                                ],
                                                "feature_type": "Episode",
                                                "url": "https://www.opensubtitles.com/en/tvshows/2000-waking-the-dead/seasons/4/episodes/4-waking-the-dead-false-flag-part-2",
                                                "img_url": "https://s9.osdb.link/features/7/5/8/126857.jpg",
                                                "seasons": []
                                            }
                                        },
                                        {
                                            "id": "62212",
                                            "type": "feature",
                                            "attributes": {
                                                "title": "\"Point Pleasant\" Waking the Dead",
                                                "original_title": "",
                                                "year": "2005",
                                                "subtitles_counts": {
                                                    "pl": 3,
                                                    "en": 2,
                                                    "hu": 2,
                                                    "cs": 1,
                                                    "nl": 1,
                                                    "et": 1,
                                                    "fi": 1,
                                                    "fr": 1,
                                                    "el": 1,
                                                    "pt-PT": 1,
                                                    "ro": 1,
                                                    "pt-BR": 1
                                                },
                                                "subtitles_count": 16,
                                                "seasons_count": 0,
                                                "parent_title": "Point Pleasant",
                                                "season_number": 1,
                                                "episode_number": 9,
                                                "imdb_id": 676101,
                                                "tmdb_id": "",
                                                "parent_imdb_id": 435576,
                                                "feature_id": "62212",
                                                "title_aka": [
                                                    "\"Point Pleasant\" Waking the Dead"
                                                ],
                                                "feature_type": "Episode",
                                                "url": "https://www.opensubtitles.com/en/tvshows/2005-point-pleasant/seasons/1/episodes/9-point-pleasant-waking-the-dead",
                                                "img_url": "https://s9.osdb.link/features/2/1/2/62212.jpg",
                                                "seasons": []
                                            }
                                        },
                                        {
                                            "id": "126869",
                                            "type": "feature",
                                            "attributes": {
                                                "title": "\"Waking the Dead\" Every Breath You Take: Part 2",
                                                "original_title": "",
                                                "year": "2001",
                                                "subtitles_counts": {
                                                    "en": 1,
                                                    "es": 1,
                                                    "ro": 1
                                                },
                                                "subtitles_count": 3,
                                                "seasons_count": 0,
                                                "parent_title": "Waking the Dead",
                                                "season_number": 1,
                                                "episode_number": 10,
                                                "imdb_id": 936018,
                                                "tmdb_id": "",
                                                "parent_imdb_id": 259733,
                                                "feature_id": "126869",
                                                "title_aka": [
                                                    "\"Waking the Dead\" Every Breath You Take: Part 2"
                                                ],
                                                "feature_type": "Episode",
                                                "url": "https://www.opensubtitles.com/en/tvshows/2000-waking-the-dead/seasons/1/episodes/10-waking-the-dead-every-breath-you-take-part-2",
                                                "img_url": "",
                                                "seasons": []
                                            }
                                        },
                                        {
                                            "id": "126826",
                                            "type": "feature",
                                            "attributes": {
                                                "title": "\"Waking the Dead\" Sins: Part 2",
                                                "original_title": "",
                                                "year": "2008",
                                                "subtitles_counts": {
                                                    "ru": 2,
                                                    "nl": 1,
                                                    "en": 1
                                                },
                                                "subtitles_count": 4,
                                                "seasons_count": 0,
                                                "parent_title": "Waking the Dead",
                                                "season_number": 7,
                                                "episode_number": 4,
                                                "imdb_id": 1218285,
                                                "tmdb_id": "",
                                                "parent_imdb_id": 259733,
                                                "feature_id": "126826",
                                                "title_aka": [
                                                    "\"Waking the Dead\" Sins: Part 2"
                                                ],
                                                "feature_type": "Episode",
                                                "url": "https://www.opensubtitles.com/en/tvshows/2000-waking-the-dead/seasons/7/episodes/4-waking-the-dead-sins-part-2",
                                                "img_url": "",
                                                "seasons": []
                                            }
                                        },
                                        {
                                            "id": "126837",
                                            "type": "feature",
                                            "attributes": {
                                                "title": "\"Waking the Dead\" End of the Night: Part 1",
                                                "original_title": "",
                                                "year": "2009",
                                                "subtitles_counts": {
                                                    "nl": 2,
                                                    "en": 1,
                                                    "sr": 1,
                                                    "es": 1
                                                },
                                                "subtitles_count": 5,
                                                "seasons_count": 0,
                                                "parent_title": "Waking the Dead",
                                                "season_number": 8,
                                                "episode_number": 3,
                                                "imdb_id": 1509622,
                                                "tmdb_id": "",
                                                "parent_imdb_id": 259733,
                                                "feature_id": "126837",
                                                "title_aka": [
                                                    "\"Waking the Dead\" End of the Night: Part 1"
                                                ],
                                                "feature_type": "Episode",
                                                "url": "https://www.opensubtitles.com/en/tvshows/2000-waking-the-dead/seasons/8/episodes/3-waking-the-dead-end-of-the-night-part-1",
                                                "img_url": "https://s9.osdb.link/features/7/3/8/126837.jpg",
                                                "seasons": []
                                            }
                                        }
                                    ],
                                    "value": "this is test  how it is rendered"
                                }
                            }
                        }
                    }
                },
                "deprecated": false,
                "security": [
                    {
                        "Api-Key": []
                    }
                ]
            }
        },
        "/subtitles": {
            "get": {
                "tags": [
                    "Subtitles"
                ],
                "summary": "Search for subtitles",
                "description": "Find subtitle for a video file. All parameters can be combined following various logics: searching by a specific external id (imdb, tmdb), a file moviehash, or a simple text query.\n\n<!-- theme: warning -->\n> Something wrong? Read about [common mistakes and best practices](docs/2-Best-Practices.md). \n\n> Getting no results? Follow HTTP redirects! ```curl --location``` and use verbose mode\n\n> Use ```imdb_id for``` movie or episode. Use ```parent_imdb_id``` for TV Shows\n\n\n\nImplement the logic that best fits your needs, keeping in mind the following guidelines:\n\n- If you can obtain the moviehash from the file, please send it along.\n- If you possess the ID, whether it's IMDB or TMDB, send it instead of a query, as an ID provides more precision.\n- When searching for TV show episodes, it is recommended to send the parent ID, along with the episode and season number for optimal results.  If you have the unique ID of an episode, only send this ID, excluding the episode or season number.\n- Include the filename as a query parameter along with the moviehash for improved results. If your filenames are generally irrelevant, such as dynamically generated filenames from a streaming service, there's no need to include them.\n- Consider treating parameters as filters rather than additional criteria. If you have a specific ID and send a query with conflicting data, like a wrong year, it could result in fewer matches.\n- Explore querying the /features endpoint to gather the exact list of available episodes.\n- Keep in mind that this is a collaborative project where subtitles are submitted by users, filtered by admins, and movie/show results are processed through various APIs. Occasionally, errors may occur, and we depend on user feedback to address and rectify them.\n\n\n> Avoid http redirection by sending request parameters sorted and without default values, and send all queries in lowercase. Remove leading zeroes in ID parameters (IMDB ID, TMDB ID...)\n\n### Moviehash \nIf a ```moviehash``` is sent with a request, a ```moviehash_match``` boolean field will be added to the response.\n\nThe matching subtitles will always come first in the response.\n\n\n### Ordering\n\n<!-- theme: warning -->\n> If possible, don't order results, because sorting on server is \"expensive, time consuming operation\" and also you have much higher chance to get cached result when not using this function.\n\nYou can order the results using the ```order_by``` parameter. Ordering is possible on the following fields:\n```language```, ```download_count```, ```new_download_count```, ```hearing_impaired```, ```hd```, ```fps```, ```votes```, ```points```, ```ratings```, ```from_trusted```, ```foreign_parts_only```, ```ai_translated```, ```machine_translated```, ```upload_date```, ```release```, ```comments```\n\nChange the order direction with *order_direction* (asc/desc)\n\n### Final notes\n```ai_translated``` (default include in search results) subtitles should be much better quality than ```machine_translated``` subtitles (excluded in search results).",
                "operationId": "subtitles",
                "parameters": [
                    {
                        "name": "id",
                        "in": "query",
                        "description": "ID of the movie or episode",
                        "schema": {
                            "type": "integer"
                        }
                    },
                    {
                        "name": "imdb_id",
                        "in": "query",
                        "description": "IMDB ID of the movie or episode",
                        "schema": {
                            "type": "integer"
                        }
                    },
                    {
                        "name": "tmdb_id",
                        "in": "query",
                        "description": "TMDB ID of the movie or episode",
                        "schema": {
                            "type": "integer"
                        }
                    },
                    {
                        "name": "type",
                        "in": "query",
                        "description": "movie, episode or all, (default: all) ",
                        "schema": {
                            "type": "string"
                        }
                    },
                    {
                        "name": "query",
                        "in": "query",
                        "description": "file name or text search",
                        "schema": {
                            "type": "string"
                        }
                    },
                    {
                        "name": "languages",
                        "in": "query",
                        "description": "Language code(s), comma separated, sorted in alphabetical order (en,fr)",
                        "schema": {
                            "type": "string"
                        }
                    },
                    {
                        "name": "moviehash",
                        "in": "query",
                        "description": "Moviehash of the moviefile",
                        "schema": {
                            "maxLength": 16,
                            "minLength": 16,
                            "pattern": "^[a-f0-9]{16}$",
                            "type": "string"
                        }
                    },
                    {
                        "name": "uploader_id",
                        "in": "query",
                        "description": "To be used alone - for user uploads listing",
                        "schema": {
                            "type": "integer"
                        }
                    },
                    {
                        "name": "hearing_impaired",
                        "in": "query",
                        "description": "include, exclude, only. (default: include)",
                        "schema": {
                            "type": "string"
                        }
                    },
                    {
                        "name": "foreign_parts_only",
                        "in": "query",
                        "description": "exclude, include, only (default: include)",
                        "schema": {
                            "type": "string"
                        }
                    },
                    {
                        "name": "trusted_sources",
                        "in": "query",
                        "description": "include, only (default: include)",
                        "schema": {
                            "type": "string"
                        }
                    },
                    {
                        "name": "machine_translated",
                        "in": "query",
                        "description": "exclude, include  (default: exclude)",
                        "schema": {
                            "type": "string"
                        }
                    },
                    {
                        "name": "ai_translated",
                        "in": "query",
                        "description": "exclude, include  (default: include)",
                        "schema": {
                            "type": "string"
                        }
                    },
                    {
                        "name": "order_by",
                        "in": "query",
                        "description": "Order of the returned results, accept any of above fields",
                        "schema": {
                            "type": "string"
                        }
                    },
                    {
                        "name": "order_direction",
                        "in": "query",
                        "description": "Order direction of the returned results (asc,desc)",
                        "schema": {
                            "type": "string"
                        }
                    },
                    {
                        "name": "parent_feature_id",
                        "in": "query",
                        "description": "For Tvshows",
                        "schema": {
                            "type": "integer"
                        }
                    },
                    {
                        "name": "parent_imdb_id",
                        "in": "query",
                        "description": "For Tvshows",
                        "schema": {
                            "type": "integer"
                        }
                    },
                    {
                        "name": "parent_tmdb_id",
                        "in": "query",
                        "description": "For Tvshows",
                        "schema": {
                            "type": "integer"
                        }
                    },
                    {
                        "name": "season_number",
                        "in": "query",
                        "description": "For Tvshows\n",
                        "schema": {
                            "type": "integer"
                        }
                    },
                    {
                        "name": "episode_number",
                        "in": "query",
                        "description": "For Tvshows",
                        "schema": {
                            "type": "integer"
                        }
                    },
                    {
                        "name": "year",
                        "in": "query",
                        "description": "Filter by movie/episode year",
                        "schema": {
                            "type": "integer"
                        }
                    },
                    {
                        "name": "moviehash_match",
                        "in": "query",
                        "description": "include, only (default: include)",
                        "schema": {
                            "type": "string"
                        }
                    },
                    {
                        "name": "page",
                        "in": "query",
                        "description": "Results page to display",
                        "schema": {
                            "type": "integer"
                        }
                    },
                    {
                        "schema": {
                            "type": "string"
                        },
                        "in": "header",
                        "name": "User-Agent",
                        "description": "<<{{APP_NAME}} v{{APP_VERSION}}>>"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "total_pages": {
                                            "type": "integer"
                                        },
                                        "total_count": {
                                            "type": "integer"
                                        },
                                        "per_page": {
                                            "type": "integer"
                                        },
                                        "page": {
                                            "type": "integer"
                                        },
                                        "data": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "id": {
                                                        "type": "string"
                                                    },
                                                    "type": {
                                                        "type": "string"
                                                    },
                                                    "attributes": {
                                                        "type": "object",
                                                        "properties": {
                                                            "subtitle_id": {
                                                                "type": "string"
                                                            },
                                                            "language": {
                                                                "type": "string"
                                                            },
                                                            "download_count": {
                                                                "type": "integer"
                                                            },
                                                            "new_download_count": {
                                                                "type": "integer"
                                                            },
                                                            "hearing_impaired": {
                                                                "type": "boolean"
                                                            },
                                                            "hd": {
                                                                "type": "boolean"
                                                            },
                                                            "fps": {
                                                                "type": "number"
                                                            },
                                                            "votes": {
                                                                "type": "integer"
                                                            },
                                                            "ratings": {
                                                                "type": "integer"
                                                            },
                                                            "from_trusted": {
                                                                "type": "boolean"
                                                            },
                                                            "foreign_parts_only": {
                                                                "type": "boolean"
                                                            },
                                                            "upload_date": {
                                                                "type": "string"
                                                            },
                                                            "ai_translated": {
                                                                "type": "boolean"
                                                            },
                                                            "nb_cd": {
                                                                "type": "integer"
                                                            },
                                                            "slug": {
                                                                "type": "string"
                                                            },
                                                            "machine_translated": {
                                                                "type": "boolean"
                                                            },
                                                            "release": {
                                                                "type": "string"
                                                            },
                                                            "comments": {
                                                                "type": "string"
                                                            },
                                                            "legacy_subtitle_id": {
                                                                "type": "integer"
                                                            },
                                                            "legacy_uploader_id": {
                                                                "type": "integer"
                                                            },
                                                            "uploader": {
                                                                "type": "object",
                                                                "properties": {
                                                                    "uploader_id": {
                                                                        "type": "integer"
                                                                    },
                                                                    "name": {
                                                                        "type": "string"
                                                                    },
                                                                    "rank": {
                                                                        "type": "string"
                                                                    }
                                                                }
                                                            },
                                                            "feature_details": {
                                                                "type": "object",
                                                                "properties": {
                                                                    "feature_id": {
                                                                        "type": "integer"
                                                                    },
                                                                    "feature_type": {
                                                                        "type": "string"
                                                                    },
                                                                    "year": {
                                                                        "type": "integer"
                                                                    },
                                                                    "title": {
                                                                        "type": "string"
                                                                    },
                                                                    "movie_name": {
                                                                        "type": "string"
                                                                    },
                                                                    "imdb_id": {
                                                                        "type": "integer"
                                                                    },
                                                                    "tmdb_id": {
                                                                        "type": "integer"
                                                                    },
                                                                    "season_number": {
                                                                        "type": "integer"
                                                                    },
                                                                    "episode_number": {
                                                                        "type": "integer"
                                                                    },
                                                                    "parent_imdb_id": {
                                                                        "type": "integer"
                                                                    },
                                                                    "parent_title": {
                                                                        "type": "string"
                                                                    },
                                                                    "parent_tmdb_id": {
                                                                        "type": "integer"
                                                                    },
                                                                    "parent_feature_id": {
                                                                        "type": "integer"
                                                                    }
                                                                }
                                                            },
                                                            "url": {
                                                                "type": "string"
                                                            },
                                                            "related_links": {
                                                                "type": "array",
                                                                "items": {
                                                                    "type": "object",
                                                                    "properties": {
                                                                        "label": {
                                                                            "type": "string"
                                                                        },
                                                                        "url": {
                                                                            "type": "string"
                                                                        },
                                                                        "img_url": {
                                                                            "type": "string"
                                                                        }
                                                                    }
                                                                }
                                                            },
                                                            "files": {
                                                                "type": "array",
                                                                "items": {
                                                                    "type": "object",
                                                                    "properties": {
                                                                        "file_id": {
                                                                            "type": "integer"
                                                                        },
                                                                        "cd_number": {
                                                                            "type": "integer"
                                                                        },
                                                                        "file_name": {
                                                                            "type": "string"
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    "x-examples": {
                                        "Example 1": {
                                            "total_pages": 1,
                                            "total_count": 22,
                                            "per_page": 50,
                                            "page": 1,
                                            "data": [
                                                {
                                                    "id": "8520224",
                                                    "type": "subtitle",
                                                    "attributes": {
                                                        "subtitle_id": "8520224",
                                                        "language": "fr",
                                                        "download_count": 147,
                                                        "new_download_count": 77,
                                                        "hearing_impaired": false,
                                                        "hd": false,
                                                        "fps": 0,
                                                        "votes": 0,
                                                        "ratings": 0,
                                                        "from_trusted": false,
                                                        "foreign_parts_only": false,
                                                        "upload_date": "2024-06-26T07:02:57Z",
                                                        "ai_translated": false,
                                                        "nb_cd": 1,
                                                        "slug": "desperate-housewives-s01e05-come-in-stranger-vo-stfr-en-_track4",
                                                        "machine_translated": false,
                                                        "release": "Desperate Housewives S01E05 Come In, Stranger (VO+STFR&EN)_track4",
                                                        "comments": "Imported from subscene.com/subtitles/desperate-housewives-first-season/french/781305",
                                                        "legacy_subtitle_id": 10626866,
                                                        "legacy_uploader_id": 10030650,
                                                        "uploader": {
                                                            "uploader_id": null,
                                                            "name": "Anonymous",
                                                            "rank": "anonymous"
                                                        },
                                                        "feature_details": {
                                                            "feature_id": 805,
                                                            "feature_type": "Episode",
                                                            "year": 2004,
                                                            "title": "Come In, Stranger",
                                                            "movie_name": "Beautés désespérées - S01E05  La Peur au ventre",
                                                            "imdb_id": 558705,
                                                            "tmdb_id": 38366,
                                                            "season_number": 1,
                                                            "episode_number": 5,
                                                            "parent_imdb_id": 410975,
                                                            "parent_title": "Desperate Housewives",
                                                            "parent_tmdb_id": 693,
                                                            "parent_feature_id": 107
                                                        },
                                                        "url": "https://staging.opensubtitles.com/fr/subtitles/desperate-housewives-s01e05-come-in-stranger-vo-stfr-en-_track4",
                                                        "related_links": [
                                                            {
                                                                "label": "All subtitles for Tv Show Desperate Housewives",
                                                                "url": "https://www.opensubtitles.com/fr/features/redirect/107",
                                                                "img_url": "https://s3.opensubtitles.com/features/5/0/8/805.jpg"
                                                            },
                                                            {
                                                                "label": "All subtitles for Episódio come in, stranger",
                                                                "url": "https://www.opensubtitles.com/fr/features/redirect/805"
                                                            }
                                                        ],
                                                        "files": [
                                                            {
                                                                "file_id": 9443515,
                                                                "cd_number": 1,
                                                                "file_name": "Desperate Housewives S01E05 Come In_ Stranger (VO+STFR.EN)_track4_fre"
                                                            }
                                                        ]
                                                    }
                                                },
                                                {
                                                    "id": "1252961",
                                                    "type": "subtitle",
                                                    "attributes": {
                                                        "subtitle_id": "1252961",
                                                        "language": "fr",
                                                        "download_count": 3622,
                                                        "new_download_count": 131,
                                                        "hearing_impaired": false,
                                                        "hd": false,
                                                        "fps": 0,
                                                        "votes": 2,
                                                        "ratings": 10,
                                                        "from_trusted": false,
                                                        "foreign_parts_only": false,
                                                        "upload_date": "2007-03-17T17:09:51Z",
                                                        "ai_translated": false,
                                                        "nb_cd": 1,
                                                        "slug": "3111203-s01e05",
                                                        "machine_translated": false,
                                                        "release": "S01E05",
                                                        "comments": "S01E05",
                                                        "legacy_subtitle_id": 3111203,
                                                        "legacy_uploader_id": 143124,
                                                        "uploader": {
                                                            "uploader_id": 36406,
                                                            "name": "deepblue",
                                                            "rank": "gold member"
                                                        },
                                                        "feature_details": {
                                                            "feature_id": 805,
                                                            "feature_type": "Episode",
                                                            "year": 2004,
                                                            "title": "Come In, Stranger",
                                                            "movie_name": "Desperate Housewives - S01E05  Come In, Stranger",
                                                            "imdb_id": 558705,
                                                            "tmdb_id": 38366,
                                                            "season_number": 1,
                                                            "episode_number": 5,
                                                            "parent_imdb_id": 410975,
                                                            "parent_title": "Desperate Housewives",
                                                            "parent_tmdb_id": 693,
                                                            "parent_feature_id": 107
                                                        },
                                                        "url": "https://staging.opensubtitles.com/fr/subtitles/3111203-s01e05",
                                                        "related_links": [
                                                            {
                                                                "label": "All subtitles for Tv Show Desperate Housewives",
                                                                "url": "https://www.opensubtitles.com/fr/features/redirect/107",
                                                                "img_url": "https://s2.opensubtitles.com/features/5/0/8/805.jpg"
                                                            },
                                                            {
                                                                "label": "All subtitles for Episódio come in, stranger",
                                                                "url": "https://www.opensubtitles.com/fr/features/redirect/805"
                                                            }
                                                        ],
                                                        "files": [
                                                            {
                                                                "file_id": 1348525,
                                                                "cd_number": 1,
                                                                "file_name": "Desperate Housewives - s01e05.fr"
                                                            }
                                                        ]
                                                    }
                                                },
                                                {
                                                    "id": "1253367",
                                                    "type": "subtitle",
                                                    "attributes": {
                                                        "subtitle_id": "1253367",
                                                        "language": "fr",
                                                        "download_count": 1110,
                                                        "new_download_count": 37,
                                                        "hearing_impaired": false,
                                                        "hd": true,
                                                        "fps": 23.976,
                                                        "votes": 0,
                                                        "ratings": 0,
                                                        "from_trusted": false,
                                                        "foreign_parts_only": false,
                                                        "upload_date": "2010-06-09T19:21:33Z",
                                                        "ai_translated": false,
                                                        "nb_cd": 1,
                                                        "slug": "desperate-housewives-s01e05-hdtv_lol",
                                                        "machine_translated": false,
                                                        "release": "Desperate Housewives S01E05 - hdtv_lol",
                                                        "comments": "",
                                                        "legacy_subtitle_id": 3687232,
                                                        "legacy_uploader_id": 0,
                                                        "uploader": {
                                                            "uploader_id": 3282,
                                                            "name": "os-auto",
                                                            "rank": "Application Developers"
                                                        },
                                                        "feature_details": {
                                                            "feature_id": 805,
                                                            "feature_type": "Episode",
                                                            "year": 2004,
                                                            "title": "Come In, Stranger",
                                                            "movie_name": "Desperate Housewives - S01E05  Come In, Stranger",
                                                            "imdb_id": 558705,
                                                            "tmdb_id": 38366,
                                                            "season_number": 1,
                                                            "episode_number": 5,
                                                            "parent_imdb_id": 410975,
                                                            "parent_title": "Desperate Housewives",
                                                            "parent_tmdb_id": 693,
                                                            "parent_feature_id": 107
                                                        },
                                                        "url": "https://staging.opensubtitles.com/fr/subtitles/desperate-housewives-s01e05-hdtv_lol",
                                                        "related_links": [
                                                            {
                                                                "label": "All subtitles for Tv Show Desperate Housewives",
                                                                "url": "https://www.opensubtitles.com/fr/features/redirect/107",
                                                                "img_url": "https://s7.opensubtitles.com/features/5/0/8/805.jpg"
                                                            },
                                                            {
                                                                "label": "All subtitles for Episódio come in, stranger",
                                                                "url": "https://www.opensubtitles.com/fr/features/redirect/805"
                                                            }
                                                        ],
                                                        "files": [
                                                            {
                                                                "file_id": 1348886,
                                                                "cd_number": 1,
                                                                "file_name": "Desperate Housewives S01E05 - hdtv_lol"
                                                            }
                                                        ]
                                                    }
                                                },
                                                {
                                                    "id": "1254138",
                                                    "type": "subtitle",
                                                    "attributes": {
                                                        "subtitle_id": "1254138",
                                                        "language": "en",
                                                        "download_count": 5071,
                                                        "new_download_count": 550,
                                                        "hearing_impaired": false,
                                                        "hd": true,
                                                        "fps": 0,
                                                        "votes": 0,
                                                        "ratings": 0,
                                                        "from_trusted": false,
                                                        "foreign_parts_only": false,
                                                        "upload_date": "2013-12-30T23:57:41Z",
                                                        "ai_translated": false,
                                                        "nb_cd": 1,
                                                        "slug": "desperate-housewives-s01e05-720p-web-dl-dual-audio",
                                                        "machine_translated": false,
                                                        "release": "Desperate.Housewives.S01E05.720p.WEB-DL.Dual.Audio",
                                                        "comments": "",
                                                        "legacy_subtitle_id": 5468392,
                                                        "legacy_uploader_id": 0,
                                                        "uploader": {
                                                            "uploader_id": 3282,
                                                            "name": "os-auto",
                                                            "rank": "Application Developers"
                                                        },
                                                        "feature_details": {
                                                            "feature_id": 805,
                                                            "feature_type": "Episode",
                                                            "year": 2004,
                                                            "title": "Come In, Stranger",
                                                            "movie_name": "Desperate Housewives - S01E05  Come In, Stranger",
                                                            "imdb_id": 558705,
                                                            "tmdb_id": 38366,
                                                            "season_number": 1,
                                                            "episode_number": 5,
                                                            "parent_imdb_id": 410975,
                                                            "parent_title": "Desperate Housewives",
                                                            "parent_tmdb_id": 693,
                                                            "parent_feature_id": 107
                                                        },
                                                        "url": "https://staging.opensubtitles.com/en/subtitles/desperate-housewives-s01e05-720p-web-dl-dual-audio",
                                                        "related_links": [
                                                            {
                                                                "label": "All subtitles for Tv Show Desperate Housewives",
                                                                "url": "https://www.opensubtitles.com/en/features/redirect/107",
                                                                "img_url": "https://s6.opensubtitles.com/features/5/0/8/805.jpg"
                                                            },
                                                            {
                                                                "label": "All subtitles for Episódio come in, stranger",
                                                                "url": "https://www.opensubtitles.com/en/features/redirect/805"
                                                            }
                                                        ],
                                                        "files": [
                                                            {
                                                                "file_id": 1349583,
                                                                "cd_number": 1,
                                                                "file_name": "Desperate.Housewives.S01E05.720p.WEB-DL.Dual.Audio-eng"
                                                            }
                                                        ]
                                                    }
                                                },
                                                {
                                                    "id": "1253856",
                                                    "type": "subtitle",
                                                    "attributes": {
                                                        "subtitle_id": "1253856",
                                                        "language": "en",
                                                        "download_count": 25300,
                                                        "new_download_count": 1025,
                                                        "hearing_impaired": false,
                                                        "hd": false,
                                                        "fps": 30,
                                                        "votes": 0,
                                                        "ratings": 0,
                                                        "from_trusted": true,
                                                        "foreign_parts_only": false,
                                                        "upload_date": "2009-12-05T15:53:47Z",
                                                        "ai_translated": false,
                                                        "nb_cd": 1,
                                                        "slug": "4374747-desperate-housewives-s01-dvdrip-xvid-wat",
                                                        "machine_translated": false,
                                                        "release": "Desperate.Housewives.S01.DVDRip.XviD-WAT",
                                                        "comments": "",
                                                        "legacy_subtitle_id": 4374747,
                                                        "legacy_uploader_id": 510761,
                                                        "uploader": {
                                                            "uploader_id": 42455,
                                                            "name": "MrLifestyles",
                                                            "rank": "Trusted member"
                                                        },
                                                        "feature_details": {
                                                            "feature_id": 805,
                                                            "feature_type": "Episode",
                                                            "year": 2004,
                                                            "title": "Come In, Stranger",
                                                            "movie_name": "Desperate Housewives - S01E05  Come In, Stranger",
                                                            "imdb_id": 558705,
                                                            "tmdb_id": 38366,
                                                            "season_number": 1,
                                                            "episode_number": 5,
                                                            "parent_imdb_id": 410975,
                                                            "parent_title": "Desperate Housewives",
                                                            "parent_tmdb_id": 693,
                                                            "parent_feature_id": 107
                                                        },
                                                        "url": "https://staging.opensubtitles.com/en/subtitles/4374747-desperate-housewives-s01-dvdrip-xvid-wat",
                                                        "related_links": [
                                                            {
                                                                "label": "All subtitles for Tv Show Desperate Housewives",
                                                                "url": "https://www.opensubtitles.com/en/features/redirect/107",
                                                                "img_url": "https://s4.opensubtitles.com/features/5/0/8/805.jpg"
                                                            },
                                                            {
                                                                "label": "All subtitles for Episódio come in, stranger",
                                                                "url": "https://www.opensubtitles.com/en/features/redirect/805"
                                                            }
                                                        ],
                                                        "files": [
                                                            {
                                                                "file_id": 1349324,
                                                                "cd_number": 1,
                                                                "file_name": "desperate.housewives.s01e05.dvdrip.xvid-wat"
                                                            }
                                                        ]
                                                    }
                                                },
                                                {
                                                    "id": "1252764",
                                                    "type": "subtitle",
                                                    "attributes": {
                                                        "subtitle_id": "1252764",
                                                        "language": "en",
                                                        "download_count": 3459,
                                                        "new_download_count": 125,
                                                        "hearing_impaired": false,
                                                        "hd": true,
                                                        "fps": 23.976,
                                                        "votes": 1,
                                                        "ratings": 10,
                                                        "from_trusted": false,
                                                        "foreign_parts_only": false,
                                                        "upload_date": "2005-05-04T00:00:00Z",
                                                        "ai_translated": false,
                                                        "nb_cd": 1,
                                                        "slug": "156095-desperate-housewives-2004",
                                                        "machine_translated": false,
                                                        "release": "Desperate Housewives (2004)",
                                                        "comments": null,
                                                        "legacy_subtitle_id": 156095,
                                                        "legacy_uploader_id": 47419,
                                                        "uploader": {
                                                            "uploader_id": 13614,
                                                            "name": "miskon (a)",
                                                            "rank": "Platinum Member"
                                                        },
                                                        "feature_details": {
                                                            "feature_id": 805,
                                                            "feature_type": "Episode",
                                                            "year": 2004,
                                                            "title": "Come In, Stranger",
                                                            "movie_name": "Desperate Housewives - S01E05  Come In, Stranger",
                                                            "imdb_id": 558705,
                                                            "tmdb_id": 38366,
                                                            "season_number": 1,
                                                            "episode_number": 5,
                                                            "parent_imdb_id": 410975,
                                                            "parent_title": "Desperate Housewives",
                                                            "parent_tmdb_id": 693,
                                                            "parent_feature_id": 107
                                                        },
                                                        "url": "https://staging.opensubtitles.com/en/subtitles/156095-desperate-housewives-2004",
                                                        "related_links": [
                                                            {
                                                                "label": "All subtitles for Tv Show Desperate Housewives",
                                                                "url": "https://www.opensubtitles.com/en/features/redirect/107",
                                                                "img_url": "https://s9.opensubtitles.com/features/5/0/8/805.jpg"
                                                            },
                                                            {
                                                                "label": "All subtitles for Episódio come in, stranger",
                                                                "url": "https://www.opensubtitles.com/en/features/redirect/805"
                                                            }
                                                        ],
                                                        "files": [
                                                            {
                                                                "file_id": 1348351,
                                                                "cd_number": 1,
                                                                "file_name": "desperate.housewives.s01e05.hdtv-lol"
                                                            }
                                                        ]
                                                    }
                                                },
                                                {
                                                    "id": "6733990",
                                                    "type": "subtitle",
                                                    "attributes": {
                                                        "subtitle_id": "6733990",
                                                        "language": "en",
                                                        "download_count": 1427,
                                                        "new_download_count": 458,
                                                        "hearing_impaired": false,
                                                        "hd": false,
                                                        "fps": 29.97,
                                                        "votes": 0,
                                                        "ratings": 0,
                                                        "from_trusted": true,
                                                        "foreign_parts_only": false,
                                                        "upload_date": "2022-09-22T17:53:09Z",
                                                        "ai_translated": false,
                                                        "nb_cd": 1,
                                                        "slug": "desperate-housewives-s01e05-come-in-stranger-dvdrip-nonhi-cc-en-bnvst",
                                                        "machine_translated": false,
                                                        "release": "Desperate Housewives S01E05 Come in, Stranger.DVDRip.NonHI.cc.en.BNVST",
                                                        "comments": "",
                                                        "legacy_subtitle_id": 9250225,
                                                        "legacy_uploader_id": 7755957,
                                                        "uploader": {
                                                            "uploader_id": 215338,
                                                            "name": "mrtinkles",
                                                            "rank": "translator"
                                                        },
                                                        "feature_details": {
                                                            "feature_id": 805,
                                                            "feature_type": "Episode",
                                                            "year": 2004,
                                                            "title": "Come In, Stranger",
                                                            "movie_name": "Desperate Housewives - S01E05  Come In, Stranger",
                                                            "imdb_id": 558705,
                                                            "tmdb_id": 38366,
                                                            "season_number": 1,
                                                            "episode_number": 5,
                                                            "parent_imdb_id": 410975,
                                                            "parent_title": "Desperate Housewives",
                                                            "parent_tmdb_id": 693,
                                                            "parent_feature_id": 107
                                                        },
                                                        "url": "https://staging.opensubtitles.com/en/subtitles/desperate-housewives-s01e05-come-in-stranger-dvdrip-nonhi-cc-en-bnvst",
                                                        "related_links": [
                                                            {
                                                                "label": "All subtitles for Tv Show Desperate Housewives",
                                                                "url": "https://www.opensubtitles.com/en/features/redirect/107",
                                                                "img_url": "https://s2.opensubtitles.com/features/5/0/8/805.jpg"
                                                            },
                                                            {
                                                                "label": "All subtitles for Episódio come in, stranger",
                                                                "url": "https://www.opensubtitles.com/en/features/redirect/805"
                                                            }
                                                        ],
                                                        "files": [
                                                            {
                                                                "file_id": 7703193,
                                                                "cd_number": 1,
                                                                "file_name": "Desperate Housewives S01E05 Come in_ Stranger.DVDRip.NonHI.cc.en.BNVST"
                                                            }
                                                        ]
                                                    }
                                                },
                                                {
                                                    "id": "5834303",
                                                    "type": "subtitle",
                                                    "attributes": {
                                                        "subtitle_id": "5834303",
                                                        "language": "en",
                                                        "download_count": 1306,
                                                        "new_download_count": 145,
                                                        "hearing_impaired": false,
                                                        "hd": false,
                                                        "fps": 0,
                                                        "votes": 0,
                                                        "ratings": 0,
                                                        "from_trusted": false,
                                                        "foreign_parts_only": false,
                                                        "upload_date": "2021-07-07T08:19:55Z",
                                                        "ai_translated": false,
                                                        "nb_cd": 1,
                                                        "slug": "8734419-s01e05",
                                                        "machine_translated": false,
                                                        "release": "S01E05",
                                                        "comments": "",
                                                        "legacy_subtitle_id": 8734419,
                                                        "legacy_uploader_id": 0,
                                                        "uploader": {
                                                            "uploader_id": 3282,
                                                            "name": "os-auto",
                                                            "rank": "Application Developers"
                                                        },
                                                        "feature_details": {
                                                            "feature_id": 805,
                                                            "feature_type": "Episode",
                                                            "year": 2004,
                                                            "title": "Come In, Stranger",
                                                            "movie_name": "Desperate Housewives - S01E05  Come In, Stranger",
                                                            "imdb_id": 558705,
                                                            "tmdb_id": 38366,
                                                            "season_number": 1,
                                                            "episode_number": 5,
                                                            "parent_imdb_id": 410975,
                                                            "parent_title": "Desperate Housewives",
                                                            "parent_tmdb_id": 693,
                                                            "parent_feature_id": 107
                                                        },
                                                        "url": "https://staging.opensubtitles.com/en/subtitles/8734419-s01e05",
                                                        "related_links": [
                                                            {
                                                                "label": "All subtitles for Tv Show Desperate Housewives",
                                                                "url": "https://www.opensubtitles.com/en/features/redirect/107",
                                                                "img_url": "https://s5.opensubtitles.com/features/5/0/8/805.jpg"
                                                            },
                                                            {
                                                                "label": "All subtitles for Episódio come in, stranger",
                                                                "url": "https://www.opensubtitles.com/en/features/redirect/805"
                                                            }
                                                        ],
                                                        "files": [
                                                            {
                                                                "file_id": 6852001,
                                                                "cd_number": 1,
                                                                "file_name": "S01E05.eng"
                                                            }
                                                        ]
                                                    }
                                                },
                                                {
                                                    "id": "1252981",
                                                    "type": "subtitle",
                                                    "attributes": {
                                                        "subtitle_id": "1252981",
                                                        "language": "en",
                                                        "download_count": 20533,
                                                        "new_download_count": 396,
                                                        "hearing_impaired": false,
                                                        "hd": false,
                                                        "fps": 25,
                                                        "votes": 2,
                                                        "ratings": 10,
                                                        "from_trusted": false,
                                                        "foreign_parts_only": false,
                                                        "upload_date": "2007-03-17T20:52:08Z",
                                                        "ai_translated": false,
                                                        "nb_cd": 1,
                                                        "slug": "3111256-s01e05",
                                                        "machine_translated": false,
                                                        "release": "S01E05",
                                                        "comments": "S01E05",
                                                        "legacy_subtitle_id": 3111256,
                                                        "legacy_uploader_id": 143124,
                                                        "uploader": {
                                                            "uploader_id": 36406,
                                                            "name": "deepblue_",
                                                            "rank": "Super Translator"
                                                        },
                                                        "feature_details": {
                                                            "feature_id": 805,
                                                            "feature_type": "Episode",
                                                            "year": 2004,
                                                            "title": "Come In, Stranger",
                                                            "movie_name": "Desperate Housewives - S01E05  Come In, Stranger",
                                                            "imdb_id": 558705,
                                                            "tmdb_id": 38366,
                                                            "season_number": 1,
                                                            "episode_number": 5,
                                                            "parent_imdb_id": 410975,
                                                            "parent_title": "Desperate Housewives",
                                                            "parent_tmdb_id": 693,
                                                            "parent_feature_id": 107
                                                        },
                                                        "url": "https://staging.opensubtitles.com/en/subtitles/3111256-s01e05",
                                                        "related_links": [
                                                            {
                                                                "label": "All subtitles for Tv Show Desperate Housewives",
                                                                "url": "https://www.opensubtitles.com/en/features/redirect/107",
                                                                "img_url": "https://s6.opensubtitles.com/features/5/0/8/805.jpg"
                                                            },
                                                            {
                                                                "label": "All subtitles for Episódio come in, stranger",
                                                                "url": "https://www.opensubtitles.com/en/features/redirect/805"
                                                            }
                                                        ],
                                                        "files": [
                                                            {
                                                                "file_id": 1348542,
                                                                "cd_number": 1,
                                                                "file_name": "Desperate Housewives - s01e05.en"
                                                            }
                                                        ]
                                                    }
                                                },
                                                {
                                                    "id": "10567507",
                                                    "type": "subtitle",
                                                    "attributes": {
                                                        "subtitle_id": "10567507",
                                                        "language": "en",
                                                        "download_count": 1,
                                                        "new_download_count": 38,
                                                        "hearing_impaired": false,
                                                        "hd": false,
                                                        "fps": 23.976,
                                                        "votes": 0,
                                                        "ratings": 0,
                                                        "from_trusted": false,
                                                        "foreign_parts_only": false,
                                                        "upload_date": "2025-08-19T02:20:53Z",
                                                        "ai_translated": false,
                                                        "nb_cd": 1,
                                                        "slug": "13231466-desperate-housewives-s01e05-come-in-stranger-sdtv",
                                                        "machine_translated": false,
                                                        "release": "Desperate Housewives - S01E05 - Come In, Stranger SDTV",
                                                        "comments": "",
                                                        "legacy_subtitle_id": 13231466,
                                                        "legacy_uploader_id": 10452159,
                                                        "uploader": {
                                                            "uploader_id": 1091298,
                                                            "name": "voice5392",
                                                            "rank": "Silver Member"
                                                        },
                                                        "feature_details": {
                                                            "feature_id": 805,
                                                            "feature_type": "Episode",
                                                            "year": 2004,
                                                            "title": "Come In, Stranger",
                                                            "movie_name": "Desperate Housewives - S01E05  Come In, Stranger",
                                                            "imdb_id": 558705,
                                                            "tmdb_id": 38366,
                                                            "season_number": 1,
                                                            "episode_number": 5,
                                                            "parent_imdb_id": 410975,
                                                            "parent_title": "Desperate Housewives",
                                                            "parent_tmdb_id": 693,
                                                            "parent_feature_id": 107
                                                        },
                                                        "url": "https://staging.opensubtitles.com/en/subtitles/13231466-desperate-housewives-s01e05-come-in-stranger-sdtv",
                                                        "related_links": [
                                                            {
                                                                "label": "All subtitles for Tv Show Desperate Housewives",
                                                                "url": "https://www.opensubtitles.com/en/features/redirect/107",
                                                                "img_url": "https://s8.opensubtitles.com/features/5/0/8/805.jpg"
                                                            },
                                                            {
                                                                "label": "All subtitles for Episódio come in, stranger",
                                                                "url": "https://www.opensubtitles.com/en/features/redirect/805"
                                                            }
                                                        ],
                                                        "files": [
                                                            {
                                                                "file_id": 11471443,
                                                                "cd_number": 1,
                                                                "file_name": "Desperate Housewives - S01E05 - Come In_ Stranger SDTV.en"
                                                            }
                                                        ]
                                                    }
                                                },
                                                {
                                                    "id": "8520231",
                                                    "type": "subtitle",
                                                    "attributes": {
                                                        "subtitle_id": "8520231",
                                                        "language": "en",
                                                        "download_count": 4933,
                                                        "new_download_count": 930,
                                                        "hearing_impaired": false,
                                                        "hd": false,
                                                        "fps": 0,
                                                        "votes": 0,
                                                        "ratings": 0,
                                                        "from_trusted": false,
                                                        "foreign_parts_only": false,
                                                        "upload_date": "2024-07-26T05:23:48Z",
                                                        "ai_translated": false,
                                                        "nb_cd": 1,
                                                        "slug": "desperate-housewives-s01e05-webrip-x264-ion10-en",
                                                        "machine_translated": false,
                                                        "release": "Desperate.Housewives.S01E05.WEBRip.x264-ION10",
                                                        "comments": "Fixed Casing and Common Errors | HI Removed\nImported from subscene.com/subtitles/desperate-housewives-first-season/english/2197737",
                                                        "legacy_subtitle_id": 12554122,
                                                        "legacy_uploader_id": 10030650,
                                                        "uploader": {
                                                            "uploader_id": null,
                                                            "name": "Anonymous",
                                                            "rank": "anonymous"
                                                        },
                                                        "feature_details": {
                                                            "feature_id": 805,
                                                            "feature_type": "Episode",
                                                            "year": 2004,
                                                            "title": "Come In, Stranger",
                                                            "movie_name": "Desperate Housewives - S01E05  Come In, Stranger",
                                                            "imdb_id": 558705,
                                                            "tmdb_id": 38366,
                                                            "season_number": 1,
                                                            "episode_number": 5,
                                                            "parent_imdb_id": 410975,
                                                            "parent_title": "Desperate Housewives",
                                                            "parent_tmdb_id": 693,
                                                            "parent_feature_id": 107
                                                        },
                                                        "url": "https://staging.opensubtitles.com/en/subtitles/desperate-housewives-s01e05-webrip-x264-ion10-en",
                                                        "related_links": [
                                                            {
                                                                "label": "All subtitles for Tv Show Desperate Housewives",
                                                                "url": "https://www.opensubtitles.com/en/features/redirect/107",
                                                                "img_url": "https://s8.opensubtitles.com/features/5/0/8/805.jpg"
                                                            },
                                                            {
                                                                "label": "All subtitles for Episódio come in, stranger",
                                                                "url": "https://www.opensubtitles.com/en/features/redirect/805"
                                                            }
                                                        ],
                                                        "files": [
                                                            {
                                                                "file_id": 9443522,
                                                                "cd_number": 1,
                                                                "file_name": "Desperate.Housewives.S01E05.WEBRip.x264-ION10"
                                                            }
                                                        ]
                                                    }
                                                },
                                                {
                                                    "id": "1254251",
                                                    "type": "subtitle",
                                                    "attributes": {
                                                        "subtitle_id": "1254251",
                                                        "language": "en",
                                                        "download_count": 6245,
                                                        "new_download_count": 298,
                                                        "hearing_impaired": false,
                                                        "hd": false,
                                                        "fps": 0,
                                                        "votes": 0,
                                                        "ratings": 0,
                                                        "from_trusted": false,
                                                        "foreign_parts_only": false,
                                                        "upload_date": "2014-03-05T21:51:00Z",
                                                        "ai_translated": false,
                                                        "nb_cd": 1,
                                                        "slug": "desperate-housewives-s01e05-xvid-hdrip-rus-eng-sbro",
                                                        "machine_translated": false,
                                                        "release": "Desperate.Housewives.S01E05.XviD.HDRip.Rus.Eng.-SBRO",
                                                        "comments": "",
                                                        "legacy_subtitle_id": 5570830,
                                                        "legacy_uploader_id": 0,
                                                        "uploader": {
                                                            "uploader_id": 3282,
                                                            "name": "os-auto",
                                                            "rank": "Application Developers"
                                                        },
                                                        "feature_details": {
                                                            "feature_id": 805,
                                                            "feature_type": "Episode",
                                                            "year": 2004,
                                                            "title": "Come In, Stranger",
                                                            "movie_name": "Desperate Housewives - S01E05  Come In, Stranger",
                                                            "imdb_id": 558705,
                                                            "tmdb_id": 38366,
                                                            "season_number": 1,
                                                            "episode_number": 5,
                                                            "parent_imdb_id": 410975,
                                                            "parent_title": "Desperate Housewives",
                                                            "parent_tmdb_id": 693,
                                                            "parent_feature_id": 107
                                                        },
                                                        "url": "https://staging.opensubtitles.com/en/subtitles/desperate-housewives-s01e05-xvid-hdrip-rus-eng-sbro",
                                                        "related_links": [
                                                            {
                                                                "label": "All subtitles for Tv Show Desperate Housewives",
                                                                "url": "https://www.opensubtitles.com/en/features/redirect/107",
                                                                "img_url": "https://s3.opensubtitles.com/features/5/0/8/805.jpg"
                                                            },
                                                            {
                                                                "label": "All subtitles for Episódio come in, stranger",
                                                                "url": "https://www.opensubtitles.com/en/features/redirect/805"
                                                            }
                                                        ],
                                                        "files": [
                                                            {
                                                                "file_id": 1349681,
                                                                "cd_number": 1,
                                                                "file_name": "Desperate.Housewives.S01E05.XviD.HDRip.Rus.Eng.-SBRO.en"
                                                            }
                                                        ]
                                                    }
                                                },
                                                {
                                                    "id": "1253664",
                                                    "type": "subtitle",
                                                    "attributes": {
                                                        "subtitle_id": "1253664",
                                                        "language": "en",
                                                        "download_count": 5933,
                                                        "new_download_count": 120,
                                                        "hearing_impaired": false,
                                                        "hd": false,
                                                        "fps": 23.976,
                                                        "votes": 1,
                                                        "ratings": 1,
                                                        "from_trusted": false,
                                                        "foreign_parts_only": false,
                                                        "upload_date": "2005-04-05T00:00:00Z",
                                                        "ai_translated": false,
                                                        "nb_cd": 1,
                                                        "slug": "4279160-desperate-housewives",
                                                        "machine_translated": false,
                                                        "release": "Desperate Housewives",
                                                        "comments": null,
                                                        "legacy_subtitle_id": 4279160,
                                                        "legacy_uploader_id": 50257,
                                                        "uploader": {
                                                            "uploader_id": 16457,
                                                            "name": "bugmenot (a)",
                                                            "rank": "Sub leecher"
                                                        },
                                                        "feature_details": {
                                                            "feature_id": 805,
                                                            "feature_type": "Episode",
                                                            "year": 2004,
                                                            "title": "Come In, Stranger",
                                                            "movie_name": "Esposas desesperadas - S01E05  Entra, desconocido",
                                                            "imdb_id": 558705,
                                                            "tmdb_id": 38366,
                                                            "season_number": 1,
                                                            "episode_number": 5,
                                                            "parent_imdb_id": 410975,
                                                            "parent_title": "Desperate Housewives",
                                                            "parent_tmdb_id": 693,
                                                            "parent_feature_id": 107
                                                        },
                                                        "url": "https://staging.opensubtitles.com/en/subtitles/4279160-desperate-housewives",
                                                        "related_links": [
                                                            {
                                                                "label": "All subtitles for Tv Show Desperate Housewives",
                                                                "url": "https://www.opensubtitles.com/en/features/redirect/107",
                                                                "img_url": "https://s7.opensubtitles.com/features/5/0/8/805.jpg"
                                                            },
                                                            {
                                                                "label": "All subtitles for Episódio come in, stranger",
                                                                "url": "https://www.opensubtitles.com/en/features/redirect/805"
                                                            }
                                                        ],
                                                        "files": [
                                                            {
                                                                "file_id": 1349152,
                                                                "cd_number": 1,
                                                                "file_name": "Desperate housewives 01x05 Come in_ stranger.en"
                                                            }
                                                        ]
                                                    }
                                                },
                                                {
                                                    "id": "10250861",
                                                    "type": "subtitle",
                                                    "attributes": {
                                                        "subtitle_id": "10250861",
                                                        "language": "en",
                                                        "download_count": 1,
                                                        "new_download_count": 0,
                                                        "hearing_impaired": false,
                                                        "hd": true,
                                                        "fps": 0,
                                                        "votes": 0,
                                                        "ratings": 0,
                                                        "from_trusted": false,
                                                        "foreign_parts_only": false,
                                                        "upload_date": "2024-07-17T13:03:38Z",
                                                        "ai_translated": false,
                                                        "nb_cd": 1,
                                                        "slug": "namae-o-nakushita-megami-e05-1080p-lk",
                                                        "machine_translated": false,
                                                        "release": "Namae.o.Nakushita.Megami.E05.1080p-lk",
                                                        "comments": "viu subs\nImported from subscene.com/subtitles/desperate-motherhood-namae-o-nakushita-megami/english/1833712",
                                                        "legacy_subtitle_id": 11880234,
                                                        "legacy_uploader_id": 10030650,
                                                        "uploader": {
                                                            "uploader_id": null,
                                                            "name": "Anonymous",
                                                            "rank": "anonymous"
                                                        },
                                                        "feature_details": {
                                                            "feature_id": 702167,
                                                            "feature_type": "Episode",
                                                            "year": 2011,
                                                            "title": "Red tears of the entrance exam crazy moms",
                                                            "movie_name": "Desperate Motherhood - S01E05  Red tears of the entrance exam crazy moms",
                                                            "imdb_id": 1928790,
                                                            "tmdb_id": 1670799,
                                                            "season_number": 1,
                                                            "episode_number": 5,
                                                            "parent_imdb_id": 1850149,
                                                            "parent_title": "Desperate Motherhood",
                                                            "parent_tmdb_id": 81571,
                                                            "parent_feature_id": 702162
                                                        },
                                                        "url": "https://staging.opensubtitles.com/en/subtitles/namae-o-nakushita-megami-e05-1080p-lk",
                                                        "related_links": [
                                                            {
                                                                "label": "All subtitles for Tv Show Desperate Motherhood",
                                                                "url": "https://www.opensubtitles.com/en/features/redirect/702162",
                                                                "img_url": "https://s9.opensubtitles.com/features/7/6/1/702167.jpg"
                                                            },
                                                            {
                                                                "label": "All subtitles for Episódio red tears of the entrance exam crazy moms",
                                                                "url": "https://www.opensubtitles.com/en/features/redirect/702167"
                                                            }
                                                        ],
                                                        "files": [
                                                            {
                                                                "file_id": 11157699,
                                                                "cd_number": 1,
                                                                "file_name": "Namae.o.Nakushita.Megami.E05.1080p-lk"
                                                            }
                                                        ]
                                                    }
                                                },
                                                {
                                                    "id": "4674561",
                                                    "type": "subtitle",
                                                    "attributes": {
                                                        "subtitle_id": "4674561",
                                                        "language": "en",
                                                        "download_count": 25,
                                                        "new_download_count": 11,
                                                        "hearing_impaired": false,
                                                        "hd": false,
                                                        "fps": 29.97,
                                                        "votes": 0,
                                                        "ratings": 0,
                                                        "from_trusted": false,
                                                        "foreign_parts_only": false,
                                                        "upload_date": "2019-01-19T23:36:17Z",
                                                        "ai_translated": false,
                                                        "nb_cd": 1,
                                                        "slug": "desperate-motherhood-e05-web-x264-walmart",
                                                        "machine_translated": false,
                                                        "release": "Desperate.Motherhood.E05.WEB.x264-WaLMaRT",
                                                        "comments": "",
                                                        "legacy_subtitle_id": 7621873,
                                                        "legacy_uploader_id": 0,
                                                        "uploader": {
                                                            "uploader_id": 3282,
                                                            "name": "os-auto",
                                                            "rank": "Application Developers"
                                                        },
                                                        "feature_details": {
                                                            "feature_id": 702167,
                                                            "feature_type": "Episode",
                                                            "year": 2011,
                                                            "title": "Red tears of the entrance exam crazy moms",
                                                            "movie_name": "Desperate Motherhood - S01E05  Red tears of the entrance exam crazy moms",
                                                            "imdb_id": 1928790,
                                                            "tmdb_id": 1670799,
                                                            "season_number": 1,
                                                            "episode_number": 5,
                                                            "parent_imdb_id": 1850149,
                                                            "parent_title": "Desperate Motherhood",
                                                            "parent_tmdb_id": 81571,
                                                            "parent_feature_id": 702162
                                                        },
                                                        "url": "https://staging.opensubtitles.com/en/subtitles/desperate-motherhood-e05-web-x264-walmart",
                                                        "related_links": [
                                                            {
                                                                "label": "All subtitles for Tv Show Desperate Motherhood",
                                                                "url": "https://www.opensubtitles.com/en/features/redirect/702162",
                                                                "img_url": "https://s5.opensubtitles.com/features/7/6/1/702167.jpg"
                                                            },
                                                            {
                                                                "label": "All subtitles for Episódio red tears of the entrance exam crazy moms",
                                                                "url": "https://www.opensubtitles.com/en/features/redirect/702167"
                                                            }
                                                        ],
                                                        "files": [
                                                            {
                                                                "file_id": 4797608,
                                                                "cd_number": 1,
                                                                "file_name": "Desperate.Motherhood.E05.WEB.x264-WaLMaRT_eng"
                                                            }
                                                        ]
                                                    }
                                                },
                                                {
                                                    "id": "3145210",
                                                    "type": "subtitle",
                                                    "attributes": {
                                                        "subtitle_id": "3145210",
                                                        "language": "en",
                                                        "download_count": 1327,
                                                        "new_download_count": 68,
                                                        "hearing_impaired": false,
                                                        "hd": false,
                                                        "fps": 0,
                                                        "votes": 0,
                                                        "ratings": 0,
                                                        "from_trusted": false,
                                                        "foreign_parts_only": false,
                                                        "upload_date": "2011-08-15T10:08:15Z",
                                                        "ai_translated": false,
                                                        "nb_cd": 1,
                                                        "slug": "desperate-romantics-01x05-dvdrip-haggis",
                                                        "machine_translated": false,
                                                        "release": "Desperate Romantics - 01x05.DVDRip HAGGiS",
                                                        "comments": "USERLOAD AUTOUPLOAD",
                                                        "legacy_subtitle_id": 4223342,
                                                        "legacy_uploader_id": 0,
                                                        "uploader": {
                                                            "uploader_id": 3282,
                                                            "name": "os-auto",
                                                            "rank": "Application Developers"
                                                        },
                                                        "feature_details": {
                                                            "feature_id": 230323,
                                                            "feature_type": "Episode",
                                                            "year": 2009,
                                                            "title": "Episode 5",
                                                            "movie_name": "Desperate Romantics - S01E05  Episode 5",
                                                            "imdb_id": 1440475,
                                                            "tmdb_id": 599282,
                                                            "season_number": 1,
                                                            "episode_number": 5,
                                                            "parent_imdb_id": 1346018,
                                                            "parent_title": "Desperate Romantics",
                                                            "parent_tmdb_id": 21699,
                                                            "parent_feature_id": 10085
                                                        },
                                                        "url": "https://staging.opensubtitles.com/en/subtitles/desperate-romantics-01x05-dvdrip-haggis",
                                                        "related_links": [
                                                            {
                                                                "label": "All subtitles for Tv Show Desperate Romantics",
                                                                "url": "https://www.opensubtitles.com/en/features/redirect/10085",
                                                                "img_url": "https://s6.opensubtitles.com/features/3/2/3/230323.jpg"
                                                            },
                                                            {
                                                                "label": "All subtitles for Episódio episode 5",
                                                                "url": "https://www.opensubtitles.com/en/features/redirect/230323"
                                                            }
                                                        ],
                                                        "files": [
                                                            {
                                                                "file_id": 3214878,
                                                                "cd_number": 1,
                                                                "file_name": "Desperate Romantics - 01x05 - Episode 5.DVDRip HAGGiS.English.updated.Addic7ed.com"
                                                            }
                                                        ]
                                                    }
                                                },
                                                {
                                                    "id": "10250862",
                                                    "type": "subtitle",
                                                    "attributes": {
                                                        "subtitle_id": "10250862",
                                                        "language": "en",
                                                        "download_count": 1,
                                                        "new_download_count": 0,
                                                        "hearing_impaired": false,
                                                        "hd": false,
                                                        "fps": 0,
                                                        "votes": 0,
                                                        "ratings": 0,
                                                        "from_trusted": false,
                                                        "foreign_parts_only": false,
                                                        "upload_date": "2024-07-17T15:22:58Z",
                                                        "ai_translated": false,
                                                        "nb_cd": 1,
                                                        "slug": "namae-o-nakushita-megami-ep05-1280x720-x264-aac",
                                                        "machine_translated": false,
                                                        "release": "Namae o Nakushita Megami ep05 (1280x720 x264-AAC)",
                                                        "comments": "From D-Addicts. Eps 1-3, 6-11 by eidokun, eps 4-5 by emma-ba\nImported from subscene.com/subtitles/namae-o-nakushita-megami/english/1839764",
                                                        "legacy_subtitle_id": 11888602,
                                                        "legacy_uploader_id": 10030650,
                                                        "uploader": {
                                                            "uploader_id": null,
                                                            "name": "Anonymous",
                                                            "rank": "anonymous"
                                                        },
                                                        "feature_details": {
                                                            "feature_id": 702167,
                                                            "feature_type": "Episode",
                                                            "year": 2011,
                                                            "title": "Red tears of the entrance exam crazy moms",
                                                            "movie_name": "Desperate Motherhood - S01E05  Red tears of the entrance exam crazy moms",
                                                            "imdb_id": 1928790,
                                                            "tmdb_id": 1670799,
                                                            "season_number": 1,
                                                            "episode_number": 5,
                                                            "parent_imdb_id": 1850149,
                                                            "parent_title": "Desperate Motherhood",
                                                            "parent_tmdb_id": 81571,
                                                            "parent_feature_id": 702162
                                                        },
                                                        "url": "https://staging.opensubtitles.com/en/subtitles/namae-o-nakushita-megami-ep05-1280x720-x264-aac",
                                                        "related_links": [
                                                            {
                                                                "label": "All subtitles for Tv Show Desperate Motherhood",
                                                                "url": "https://www.opensubtitles.com/en/features/redirect/702162",
                                                                "img_url": "https://s2.opensubtitles.com/features/7/6/1/702167.jpg"
                                                            },
                                                            {
                                                                "label": "All subtitles for Episódio red tears of the entrance exam crazy moms",
                                                                "url": "https://www.opensubtitles.com/en/features/redirect/702167"
                                                            }
                                                        ],
                                                        "files": [
                                                            {
                                                                "file_id": 11157700,
                                                                "cd_number": 1,
                                                                "file_name": "Namae o Nakushita Megami ep05 (1280x720 x264-AAC).eng"
                                                            }
                                                        ]
                                                    }
                                                },
                                                {
                                                    "id": "10369525",
                                                    "type": "subtitle",
                                                    "attributes": {
                                                        "subtitle_id": "10369525",
                                                        "language": "en",
                                                        "download_count": 28,
                                                        "new_download_count": 5,
                                                        "hearing_impaired": false,
                                                        "hd": false,
                                                        "fps": 0,
                                                        "votes": 0,
                                                        "ratings": 0,
                                                        "from_trusted": false,
                                                        "foreign_parts_only": false,
                                                        "upload_date": "2024-06-20T09:47:05Z",
                                                        "ai_translated": false,
                                                        "nb_cd": 1,
                                                        "slug": "10254477-desperate-romantics-s01e05-hdtv-xvid-bia",
                                                        "machine_translated": false,
                                                        "release": "Desperate.Romantics.S01E05.HDTV.XviD-BiA",
                                                        "comments": "Enjoy! :)\nImported from subscene.com/subtitles/desperate-romantics-first-season/english/251833",
                                                        "legacy_subtitle_id": 10254477,
                                                        "legacy_uploader_id": 10030650,
                                                        "uploader": {
                                                            "uploader_id": null,
                                                            "name": "Anonymous",
                                                            "rank": "anonymous"
                                                        },
                                                        "feature_details": {
                                                            "feature_id": 230323,
                                                            "feature_type": "Episode",
                                                            "year": 2009,
                                                            "title": "Episode 5",
                                                            "movie_name": "Desperate Romantics - S01E05  Episode 5",
                                                            "imdb_id": 1440475,
                                                            "tmdb_id": 599282,
                                                            "season_number": 1,
                                                            "episode_number": 5,
                                                            "parent_imdb_id": 1346018,
                                                            "parent_title": "Desperate Romantics",
                                                            "parent_tmdb_id": 21699,
                                                            "parent_feature_id": 10085
                                                        },
                                                        "url": "https://staging.opensubtitles.com/en/subtitles/10254477-desperate-romantics-s01e05-hdtv-xvid-bia",
                                                        "related_links": [
                                                            {
                                                                "label": "All subtitles for Tv Show Desperate Romantics",
                                                                "url": "https://www.opensubtitles.com/en/features/redirect/10085",
                                                                "img_url": "https://s3.opensubtitles.com/features/3/2/3/230323.jpg"
                                                            },
                                                            {
                                                                "label": "All subtitles for Episódio episode 5",
                                                                "url": "https://www.opensubtitles.com/en/features/redirect/230323"
                                                            }
                                                        ],
                                                        "files": [
                                                            {
                                                                "file_id": 11275168,
                                                                "cd_number": 1,
                                                                "file_name": "Desperate.Romantics.S01E05.HDTV.XviD-BiA"
                                                            }
                                                        ]
                                                    }
                                                },
                                                {
                                                    "id": "10516581",
                                                    "type": "subtitle",
                                                    "attributes": {
                                                        "subtitle_id": "10516581",
                                                        "language": "en",
                                                        "download_count": 0,
                                                        "new_download_count": 5,
                                                        "hearing_impaired": false,
                                                        "hd": true,
                                                        "fps": 29.97,
                                                        "votes": 0,
                                                        "ratings": 0,
                                                        "from_trusted": false,
                                                        "foreign_parts_only": false,
                                                        "upload_date": "2025-07-06T10:20:10Z",
                                                        "ai_translated": false,
                                                        "nb_cd": 1,
                                                        "slug": "desperate-mrs-seonju-s01e05-241122-720p-next",
                                                        "machine_translated": false,
                                                        "release": "Desperate.Mrs.Seonju.S01E05.241122.720p-NEXT",
                                                        "comments": "Subtitles by KOCOWA.",
                                                        "legacy_subtitle_id": 13176466,
                                                        "legacy_uploader_id": 4035402,
                                                        "uploader": {
                                                            "uploader_id": 75117,
                                                            "name": "peterlin",
                                                            "rank": "Administrator"
                                                        },
                                                        "feature_details": {
                                                            "feature_id": 2784330,
                                                            "feature_type": "Episode",
                                                            "year": 2024,
                                                            "title": "Episode 5",
                                                            "movie_name": "Desperate Mrs. Seonju - S01E05  \"Desperate Mrs. Seonju\" Episode #1.5",
                                                            "imdb_id": 37062001,
                                                            "tmdb_id": null,
                                                            "season_number": 1,
                                                            "episode_number": 5,
                                                            "parent_imdb_id": 34677309,
                                                            "parent_title": "Desperate Mrs. Seonju",
                                                            "parent_tmdb_id": 261121,
                                                            "parent_feature_id": 2784328
                                                        },
                                                        "url": "https://staging.opensubtitles.com/en/subtitles/desperate-mrs-seonju-s01e05-241122-720p-next",
                                                        "related_links": [
                                                            {
                                                                "label": "All subtitles for Tv Show Desperate Mrs. Seonju",
                                                                "url": "https://www.opensubtitles.com/en/features/redirect/2784328",
                                                                "img_url": "https://s3.opensubtitles.com/features/0/3/3/2784330.jpg"
                                                            },
                                                            {
                                                                "label": "All subtitles for Episódio episode 5",
                                                                "url": "https://www.opensubtitles.com/en/features/redirect/2784330"
                                                            }
                                                        ],
                                                        "files": [
                                                            {
                                                                "file_id": 11419993,
                                                                "cd_number": 1,
                                                                "file_name": "Desperate.Mrs.Seonju.S01E05.241122.720p-NEXT_eng"
                                                            }
                                                        ]
                                                    }
                                                },
                                                {
                                                    "id": "6653421",
                                                    "type": "subtitle",
                                                    "attributes": {
                                                        "subtitle_id": "6653421",
                                                        "language": "en",
                                                        "download_count": 277,
                                                        "new_download_count": 110,
                                                        "hearing_impaired": false,
                                                        "hd": true,
                                                        "fps": 23.976,
                                                        "votes": 0,
                                                        "ratings": 0,
                                                        "from_trusted": true,
                                                        "foreign_parts_only": false,
                                                        "upload_date": "2022-07-07T14:21:57Z",
                                                        "ai_translated": false,
                                                        "nb_cd": 1,
                                                        "slug": "9161648-the-real-housewives-of-dubai-s01e05-720p-web-h264-spamneggs",
                                                        "machine_translated": false,
                                                        "release": "The.Real.Housewives.of.Dubai.S01E05.720p.WEB.H264-SPAMnEGGS",
                                                        "comments": "HI removed. (With Lyrics). Duration: 43 min 14 s. Works with the releases:\r\nThe.Real.Housewives.of.Dubai.S01E05.720p.WEB.H264-SPAMnEGGS\r\nThe.Real.Housewives.of.Dubai.S01E05.1080p.WEB.H264-SPAMnEGGS",
                                                        "legacy_subtitle_id": 9161648,
                                                        "legacy_uploader_id": 2568283,
                                                        "uploader": {
                                                            "uploader_id": 69332,
                                                            "name": "srjanapala",
                                                            "rank": "Trusted member"
                                                        },
                                                        "feature_details": {
                                                            "feature_id": 1389888,
                                                            "feature_type": "Episode",
                                                            "year": 2022,
                                                            "title": "Piping Tea With a Hint of Peach",
                                                            "movie_name": "The Real Housewives of Dubai - S01E05  Piping Tea With a Hint of Peach",
                                                            "imdb_id": 20835250,
                                                            "tmdb_id": 3812348,
                                                            "season_number": 1,
                                                            "episode_number": 5,
                                                            "parent_imdb_id": 15823202,
                                                            "parent_title": "The Real Housewives of Dubai",
                                                            "parent_tmdb_id": 196592,
                                                            "parent_feature_id": 1389533
                                                        },
                                                        "url": "https://staging.opensubtitles.com/en/subtitles/9161648-the-real-housewives-of-dubai-s01e05-720p-web-h264-spamneggs",
                                                        "related_links": [
                                                            {
                                                                "label": "All subtitles for Tv Show The Real Housewives of Dubai",
                                                                "url": "https://www.opensubtitles.com/en/features/redirect/1389533",
                                                                "img_url": "https://s9.opensubtitles.com/features/8/8/8/1389888.jpg"
                                                            },
                                                            {
                                                                "label": "All subtitles for Episódio piping tea with a hint of peach",
                                                                "url": "https://www.opensubtitles.com/en/features/redirect/1389888"
                                                            }
                                                        ],
                                                        "files": [
                                                            {
                                                                "file_id": 7622572,
                                                                "cd_number": 1,
                                                                "file_name": "The.Real.Housewives.of.Dubai.S01E05.720p.WEB.H264-SPAMnEGGS - No HI"
                                                            }
                                                        ]
                                                    }
                                                },
                                                {
                                                    "id": "6552485",
                                                    "type": "subtitle",
                                                    "attributes": {
                                                        "subtitle_id": "6552485",
                                                        "language": "en",
                                                        "download_count": 2213,
                                                        "new_download_count": 455,
                                                        "hearing_impaired": false,
                                                        "hd": true,
                                                        "fps": 25,
                                                        "votes": 0,
                                                        "ratings": 0,
                                                        "from_trusted": false,
                                                        "foreign_parts_only": false,
                                                        "upload_date": "2020-10-07T21:48:05Z",
                                                        "ai_translated": false,
                                                        "nb_cd": 1,
                                                        "slug": "the-real-housewives-of-beverly-hills-s01e05-i-would-never-say-that",
                                                        "machine_translated": false,
                                                        "release": "The Real Housewives of Beverly Hills.S01E05.I Would Never Say That",
                                                        "comments": "",
                                                        "legacy_subtitle_id": 8380434,
                                                        "legacy_uploader_id": 0,
                                                        "uploader": {
                                                            "uploader_id": 3282,
                                                            "name": "os-auto",
                                                            "rank": "Application Developers"
                                                        },
                                                        "feature_details": {
                                                            "feature_id": 1372534,
                                                            "feature_type": "Episode",
                                                            "year": 2010,
                                                            "title": "I Would Never Say That",
                                                            "movie_name": "The Real Housewives of Beverly Hills - S01E05  I Would Never Say That",
                                                            "imdb_id": 1761988,
                                                            "tmdb_id": 766076,
                                                            "season_number": 1,
                                                            "episode_number": 5,
                                                            "parent_imdb_id": 1720601,
                                                            "parent_title": "The Real Housewives of Beverly Hills",
                                                            "parent_tmdb_id": 32390,
                                                            "parent_feature_id": 1084860
                                                        },
                                                        "url": "https://staging.opensubtitles.com/en/subtitles/the-real-housewives-of-beverly-hills-s01e05-i-would-never-say-that",
                                                        "related_links": [
                                                            {
                                                                "label": "All subtitles for Tv Show The Real Housewives of Beverly Hills",
                                                                "url": "https://www.opensubtitles.com/en/features/redirect/1084860",
                                                                "img_url": "https://s2.opensubtitles.com/features/4/3/5/1372534.jpg"
                                                            },
                                                            {
                                                                "label": "All subtitles for Episódio i would never say that",
                                                                "url": "https://www.opensubtitles.com/en/features/redirect/1372534"
                                                            }
                                                        ],
                                                        "files": [
                                                            {
                                                                "file_id": 7521846,
                                                                "cd_number": 1,
                                                                "file_name": "The Real Housewives of Beverly Hills.S01E05.I Would Never Say That"
                                                            }
                                                        ]
                                                    }
                                                },
                                                {
                                                    "id": "5603793",
                                                    "type": "subtitle",
                                                    "attributes": {
                                                        "subtitle_id": "5603793",
                                                        "language": "en",
                                                        "download_count": 522,
                                                        "new_download_count": 183,
                                                        "hearing_impaired": false,
                                                        "hd": true,
                                                        "fps": 23.976,
                                                        "votes": 0,
                                                        "ratings": 0,
                                                        "from_trusted": true,
                                                        "foreign_parts_only": false,
                                                        "upload_date": "2020-12-10T17:22:29Z",
                                                        "ai_translated": false,
                                                        "nb_cd": 1,
                                                        "slug": "the-real-housewives-of-salt-lake-city-s01e05-ladies-who-lunch-1080p-amzn-web-dl-ddp5-1-h-264-ntb-en",
                                                        "machine_translated": false,
                                                        "release": "The.Real.Housewives.of.Salt.Lake.City.S01E05.Ladies.Who.Lunch.1080p.AMZN.WEB-DL.DDP5.1.H.264-NTb",
                                                        "comments": "Hi Removed - Works with all WEB-DL/WEBRip",
                                                        "legacy_subtitle_id": 8455084,
                                                        "legacy_uploader_id": 7650378,
                                                        "uploader": {
                                                            "uploader_id": 216980,
                                                            "name": "oakislandtk",
                                                            "rank": "Trusted member"
                                                        },
                                                        "feature_details": {
                                                            "feature_id": 1192341,
                                                            "feature_type": "Episode",
                                                            "year": 2020,
                                                            "title": "Ladies Who Lunch",
                                                            "movie_name": "The Real Housewives of Salt Lake City - S01E05  Ladies Who Lunch",
                                                            "imdb_id": 13492400,
                                                            "tmdb_id": 2551243,
                                                            "season_number": 1,
                                                            "episode_number": 5,
                                                            "parent_imdb_id": 11363282,
                                                            "parent_title": "The Real Housewives of Salt Lake City",
                                                            "parent_tmdb_id": 110381,
                                                            "parent_feature_id": 1192340
                                                        },
                                                        "url": "https://staging.opensubtitles.com/en/subtitles/the-real-housewives-of-salt-lake-city-s01e05-ladies-who-lunch-1080p-amzn-web-dl-ddp5-1-h-264-ntb-en",
                                                        "related_links": [
                                                            {
                                                                "label": "All subtitles for Tv Show The Real Housewives of Salt Lake City",
                                                                "url": "https://www.opensubtitles.com/en/features/redirect/1192340",
                                                                "img_url": "https://s4.opensubtitles.com/features/1/4/3/1192341.jpg"
                                                            },
                                                            {
                                                                "label": "All subtitles for Episódio ladies who lunch",
                                                                "url": "https://www.opensubtitles.com/en/features/redirect/1192341"
                                                            }
                                                        ],
                                                        "files": [
                                                            {
                                                                "file_id": 6639854,
                                                                "cd_number": 1,
                                                                "file_name": "The.Real.Housewives.of.Salt.Lake.City.S01E05.Ladies.Who.Lunch.1080p.AMZN.WEB-DL.DDP5.1.H.264-NTb"
                                                            }
                                                        ]
                                                    }
                                                }
                                            ]
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "deprecated": false,
                "security": [
                    {
                        "Api-Key": []
                    }
                ]
            }
        },
        "/download": {
            "post": {
                "tags": [
                    "Download"
                ],
                "summary": "Download",
                "description": "Request a download url for a subtitle. Subtitle file in temporary URL will be always in UTF-8 encoding.\n\n<!-- theme: warning -->\n\n> VERY IMPORTANT: In HTTP request must be both headers: ```Api-Key``` and ```Authorization``` stoplight.io doesn't allow to use in shown example both headers\n\n\n> The download count is calculated on this action, not the file download itself\n\n> IN and OUT FPS must be indicated for subtitle conversions, we want to make sure you know what you are doing, and therefore collected the current FPS from the subtitle search result, or calculated it somehow.\n\n<!-- theme: warning -->\n\n> The download URL is temporary, and cannot be used more than 3 hours, so do not cache it, but you can download the file more than once if needed.",
                "operationId": "download",
                "parameters": [
                    {
                        "schema": {
                            "type": "string"
                        },
                        "in": "header",
                        "name": "User-Agent",
                        "description": "<<{{APP_NAME}} v{{APP_VERSION}}>>"
                    }
                ],
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "x-examples": {
                                    "example-1": {
                                        "file_id": "",
                                        "sub_format": "",
                                        "file_name": "",
                                        "in_fps": "",
                                        "out_fps": "",
                                        "timeshift": "",
                                        "force_download": ""
                                    }
                                },
                                "required": [
                                    "file_id"
                                ],
                                "properties": {
                                    "file_id": {
                                        "type": "integer",
                                        "description": "file_id from /subtitles search results",
                                        "format": "int32",
                                        "example": 123
                                    },
                                    "sub_format": {
                                        "type": "string",
                                        "description": "from /infos/formats"
                                    },
                                    "file_name": {
                                        "type": "string",
                                        "description": "desired file name"
                                    },
                                    "in_fps": {
                                        "type": "number",
                                        "description": "used for conversions, in_fps and out_fps must then be indicated"
                                    },
                                    "out_fps": {
                                        "type": "number",
                                        "description": "used for conversions, in_fps and out_fps must then be indicated"
                                    },
                                    "timeshift": {
                                        "type": "number",
                                        "description": "delay to add or remove to the subtitle, + or - value, in seconds, i.e. 2.5s or -1s "
                                    },
                                    "force_download": {
                                        "type": "boolean",
                                        "description": "(1/0) set subtitle file headers to \"application/force-download\""
                                    }
                                }
                            },
                            "examples": {
                                "example-1": {
                                    "value": {
                                        "file_id": 123
                                    }
                                }
                            }
                        }
                    },
                    "required": false,
                    "description": ""
                },
                "responses": {
                    "200": {
                        "description": "Request a download URL for a subtitle. \n",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "description": "",
                                    "type": "object",
                                    "properties": {
                                        "link": {
                                            "type": "string",
                                            "minLength": 1
                                        },
                                        "file_name": {
                                            "type": "string",
                                            "minLength": 1
                                        },
                                        "requests": {
                                            "type": "number"
                                        },
                                        "remaining": {
                                            "type": "number"
                                        },
                                        "message": {
                                            "type": "string",
                                            "minLength": 1
                                        },
                                        "reset_time": {
                                            "type": "string",
                                            "minLength": 1
                                        },
                                        "reset_time_utc": {
                                            "type": "string",
                                            "minLength": 1
                                        }
                                    },
                                    "required": [
                                        "link",
                                        "file_name",
                                        "requests",
                                        "remaining",
                                        "message",
                                        "reset_time",
                                        "reset_time_utc"
                                    ],
                                    "x-examples": {
                                        "example-1": {
                                            "link": "https://www.opensubtitles.com/download/A184A5EA6302F2CA7FD9D49BCEA49A1F36662BBEFB8C9B0ECDC9BB6CAF4BF09A5AA8D7B95C7FBD01615021D1973BAC18D431A8E6A1F627E4617341E8508A6968532088A68B6DDDA996C0116E2CE6F778ED9096A9CAB942B42B59C4EA93F1A7D61FCD6CBBC29C720EBD40CE674A55375862F00981E5D2F315A0982766A2004E0ED0AD9ADABEB506A638F1B829DBC2BE15979F22DA123523967F4D4069BC32098F1086F09AAA776CC365ED744633FD5FA7160B65A2C83539DF30134F5BE6272E46019AF9FD2423AFE12E1DC8642CDB56B8FEB9A4C1F30BF68EF431A3D4ABD3A7E44559E3E572210E5A5A33EC282D3445C537C5DA9DA598300A9900FA1B3B92983FD1504FDDFB34F89E409BF03EC662FC5734F25843C277A64B7C603156926FC6C74AA1D14AABEA6E20/subfile/castle.rock.s01e03.webrip.x264-tbs.ettv.-eng.ro.srt",
                                            "file_name": "castle.rock.s01e03.webrip.x264-tbs.ettv.-eng.ro.srt",
                                            "requests": 3,
                                            "remaining": 97,
                                            "message": "Your quota will be renewed in 07 hours and 40 minutes (2022-04-08 13:03:15 UTC) ",
                                            "reset_time": "07 hours and 40 minutes",
                                            "reset_time_utc": "2022-04-08T13:03:15.000Z"
                                        }
                                    }
                                },
                                "examples": {
                                    "example-1": {
                                        "value": {
                                            "link": "https://www.opensubtitles.com/download/A184A5EA6302F2CA7FD9D49BCEA49A1F36662BBEFB8C9B0ECDC9BB6CAF4BF09A5AA8D7B95C7FBD01615021D1973BAC18D431A8E6A1F627E4617341E8508A6968532088A68B6DDDA996C0116E2CE6F778ED9096A9CAB942B42B59C4EA93F1A7D61FCD6CBBC29C720EBD40CE674A55375862F00981E5D2F315A0982766A2004E0ED0AD9ADABEB506A638F1B829DBC2BE15979F22DA123523967F4D4069BC32098F1086F09AAA776CC365ED744633FD5FA7160B65A2C83539DF30134F5BE6272E46019AF9FD2423AFE12E1DC8642CDB56B8FEB9A4C1F30BF68EF431A3D4ABD3A7E44559E3E572210E5A5A33EC282D3445C537C5DA9DA598300A9900FA1B3B92983FD1504FDDFB34F89E409BF03EC662FC5734F25843C277A64B7C603156926FC6C74AA1D14AABEA6E20/subfile/castle.rock.s01e03.webrip.x264-tbs.ettv.-eng.ro.srt",
                                            "file_name": "castle.rock.s01e03.webrip.x264-tbs.ettv.-eng.ro.srt",
                                            "requests": 3,
                                            "remaining": 97,
                                            "message": "Your quota will be renewed in 07 hours and 30 minutes (2022-04-08 13:03:16 UTC) ",
                                            "reset_time": "07 hours and 30 minutes",
                                            "reset_time_utc": "2022-04-08T13:03:16.000Z"
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "deprecated": false,
                "security": [
                    {
                        "Bearer": []
                    },
                    {
                        "Api-Key": []
                    }
                ],
                "x-codegen-request-body-name": "body"
            },
            "parameters": []
        },
        "/utilities/guessit": {
            "get": {
                "tags": [
                    "Utilities"
                ],
                "summary": "Guessit",
                "description": "Extracts as much information as possible from a video filename.\n\nIt has a very powerful matcher that allows to guess properties from a video using its filename only. This matcher works with both movies and tv shows episodes.\n\nThis is a simple implementation of the python guessit library.\nhttps://guessit-io.github.io/guessit/\n\nFind examples of the returned data.\nhttps://guessit-io.github.io/guessit/properties/",
                "operationId": "guessit",
                "parameters": [
                    {
                        "name": "filename",
                        "in": "query",
                        "description": "File name",
                        "schema": {
                            "type": "string"
                        }
                    },
                    {
                        "schema": {
                            "type": "string"
                        },
                        "in": "header",
                        "name": "User-Agent",
                        "description": "<<{{APP_NAME}} v{{APP_VERSION}}>>"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "required": [
                                        "audio_channels",
                                        "audio_codec",
                                        "language",
                                        "other",
                                        "release_group",
                                        "screen_size",
                                        "source",
                                        "streaming_service",
                                        "subtitle_language",
                                        "title",
                                        "type",
                                        "video_codec",
                                        "year"
                                    ],
                                    "type": "object",
                                    "properties": {
                                        "title": {
                                            "minLength": 1,
                                            "type": "string"
                                        },
                                        "year": {
                                            "type": "number"
                                        },
                                        "language": {
                                            "minLength": 1,
                                            "type": "string"
                                        },
                                        "subtitle_language": {
                                            "minLength": 1,
                                            "type": "string"
                                        },
                                        "screen_size": {
                                            "minLength": 1,
                                            "type": "string"
                                        },
                                        "streaming_service": {
                                            "minLength": 1,
                                            "type": "string"
                                        },
                                        "source": {
                                            "minLength": 1,
                                            "type": "string"
                                        },
                                        "other": {
                                            "minLength": 1,
                                            "type": "string"
                                        },
                                        "audio_codec": {
                                            "minLength": 1,
                                            "type": "string"
                                        },
                                        "audio_channels": {
                                            "minLength": 1,
                                            "type": "string"
                                        },
                                        "video_codec": {
                                            "minLength": 1,
                                            "type": "string"
                                        },
                                        "release_group": {
                                            "minLength": 1,
                                            "type": "string"
                                        },
                                        "type": {
                                            "minLength": 1,
                                            "type": "string"
                                        }
                                    },
                                    "description": ""
                                }
                            }
                        }
                    }
                },
                "security": [
                    {
                        "Api-Key": []
                    }
                ]
            }
        },
        "/ai/credits": {
            "get": {
                "summary": "User Credits Informations",
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "data": {
                                            "type": "object",
                                            "properties": {
                                                "credits": {
                                                    "type": "integer"
                                                }
                                            }
                                        }
                                    },
                                    "x-examples": {
                                        "Example 1": {
                                            "data": {
                                                "credits": 2019
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "operationId": "get-credits",
                "x-stoplight": {
                    "id": "hhxx9oion0rdo"
                },
                "description": "Check how much credits have logged-in user. \n[Buy Credits](../open_api.json/paths/~1ai~1credits~1buy/get)",
                "parameters": [
                    {
                        "schema": {
                            "type": "string"
                        },
                        "in": "header",
                        "name": "User-Agent",
                        "description": "<<{{APP_NAME}} v{{APP_VERSION}}>>"
                    },
                    {
                        "schema": {
                            "type": "string"
                        },
                        "in": "header",
                        "name": "Authorization",
                        "description": "Bearer <<{{token}}>>"
                    }
                ],
                "x-internal": false,
                "security": [
                    {
                        "Api-Key": []
                    }
                ],
                "tags": [
                    "User"
                ]
            }
        },
        "/ai/credits/buy": {
            "get": {
                "summary": "Buy Credits",
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "data": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "name": {
                                                        "type": "string"
                                                    },
                                                    "value": {
                                                        "type": "string"
                                                    },
                                                    "discount_percent": {
                                                        "type": "integer"
                                                    },
                                                    "checkout_url": {
                                                        "type": "string"
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    "x-examples": {
                                        "Example 1": {
                                            "data": [
                                                {
                                                    "name": "500 credits",
                                                    "value": "5 USD",
                                                    "discount_percent": 0,
                                                    "checkout_url": "https://ai.opensubtitles.com/assets/buy_credits.html?tag=1sBYypgiIshtuRhFxInoOQ%3D%3D%3AtSuW7qdTDrGra5UTHRSgWgXy8Rrg0LCb%2Fh3CxOaJpPiP%2BtmIPSA1gY3CJeM6oUc0"
                                                },
                                                {
                                                    "name": "1000 credits",
                                                    "value": "10 USD",
                                                    "discount_percent": 0,
                                                    "checkout_url": "https://ai.opensubtitles.com/assets/buy_credits.html?tag=vgBZglBSiIZUdCU2KCqsyg%3D%3D%3ALPHN%2BH1x5cBoPolx5PIkMVuEV7q025%2BWz%2FEaMv9CCM0300xkpT9f%2B3fC7d2POdso"
                                                },
                                                {
                                                    "name": "5500 credits",
                                                    "value": "50 USD",
                                                    "discount_percent": 10,
                                                    "checkout_url": "https://ai.opensubtitles.com/assets/buy_credits.html?tag=eZQKqUTXDncZLOJuIlr%2FJg%3D%3D%3AJeYPTQeow17b4%2FN4SwDJeN%2BtG4b4X%2FuO4vwjMcjWGHIMkFSXF70K8b1REsx7Ve%2B6"
                                                },
                                                {
                                                    "name": "39000 credits",
                                                    "value": "300 USD",
                                                    "discount_percent": 30,
                                                    "checkout_url": "https://ai.opensubtitles.com/assets/buy_credits.html?tag=KykrwFhYEHysP0zEJAB4pA%3D%3D%3AQ9KItCiZ8AxAPqi%2F2qIaUavVE60ANcBBLFRqFJLonMZq14xETj5GgS2lT5i4m4ri"
                                                }
                                            ]
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "operationId": "buy-credits",
                "description": "Buy credits - packages with checkout URL",
                "parameters": [
                    {
                        "schema": {
                            "type": "string"
                        },
                        "in": "header",
                        "name": "User-Agent",
                        "description": "<<{{APP_NAME}} v{{APP_VERSION}}>>"
                    },
                    {
                        "schema": {
                            "type": "string"
                        },
                        "in": "header",
                        "name": "Authorization",
                        "description": "Bearer <<{{token}}>>"
                    }
                ],
                "x-internal": false,
                "security": [
                    {
                        "Api-Key": []
                    }
                ],
                "tags": [
                    "User"
                ],
                "x-stoplight": {
                    "id": "0tuklm9ob00a3"
                }
            },
            "parameters": []
        },
        "/ai/info/translation": {
            "get": {
                "summary": "AI Translation",
                "tags": [
                    "Infos"
                ],
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "data": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "name": {
                                                        "type": "string"
                                                    },
                                                    "display_name": {
                                                        "type": "string"
                                                    },
                                                    "description": {
                                                        "type": "string"
                                                    },
                                                    "pricing": {
                                                        "type": "string"
                                                    },
                                                    "reliability": {
                                                        "type": "string"
                                                    },
                                                    "price": {
                                                        "type": "number"
                                                    },
                                                    "languages_supported": {
                                                        "type": "array",
                                                        "items": {
                                                            "type": "object",
                                                            "properties": {
                                                                "language_code": {
                                                                    "type": "string"
                                                                },
                                                                "language_name": {
                                                                    "type": "string"
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    "x-examples": {
                                        "Example 1": {
                                            "data": [
                                                {
                                                    "name": "aws",
                                                    "display_name": "Amazon Translate",
                                                    "description": "Neural machine translation by Amazon Web Service with support for many languages.",
                                                    "pricing": "Pay-per-character",
                                                    "reliability": "high",
                                                    "price": 0.0054,
                                                    "languages_supported": [
                                                        {
                                                            "language_code": "af",
                                                            "language_name": "afrikaans"
                                                        },
                                                        {
                                                            "language_code": "sq",
                                                            "language_name": "albanian"
                                                        },
                                                        {
                                                            "language_code": "am",
                                                            "language_name": "amharic"
                                                        },
                                                        {
                                                            "language_code": "ar",
                                                            "language_name": "arabic"
                                                        },
                                                        {
                                                            "language_code": "hy",
                                                            "language_name": "armenian"
                                                        },
                                                        {
                                                            "language_code": "az",
                                                            "language_name": "azerbaijani"
                                                        },
                                                        {
                                                            "language_code": "bn",
                                                            "language_name": "bengali"
                                                        },
                                                        {
                                                            "language_code": "bs",
                                                            "language_name": "bosnian"
                                                        },
                                                        {
                                                            "language_code": "bg",
                                                            "language_name": "bulgarian"
                                                        },
                                                        {
                                                            "language_code": "ca",
                                                            "language_name": "catalan"
                                                        },
                                                        {
                                                            "language_code": "zh",
                                                            "language_name": "chinese"
                                                        },
                                                        {
                                                            "language_code": "hr",
                                                            "language_name": "croatian"
                                                        },
                                                        {
                                                            "language_code": "cs",
                                                            "language_name": "czech"
                                                        },
                                                        {
                                                            "language_code": "da",
                                                            "language_name": "danish"
                                                        },
                                                        {
                                                            "language_code": "fa",
                                                            "language_name": "persian"
                                                        },
                                                        {
                                                            "language_code": "nl",
                                                            "language_name": "dutch"
                                                        },
                                                        {
                                                            "language_code": "en",
                                                            "language_name": "english"
                                                        },
                                                        {
                                                            "language_code": "et",
                                                            "language_name": "estonian"
                                                        },
                                                        {
                                                            "language_code": "tl",
                                                            "language_name": "tagalog"
                                                        },
                                                        {
                                                            "language_code": "fi",
                                                            "language_name": "finnish"
                                                        },
                                                        {
                                                            "language_code": "fr",
                                                            "language_name": "french"
                                                        },
                                                        {
                                                            "language_code": "fr-CA",
                                                            "language_name": "french (Canada)"
                                                        },
                                                        {
                                                            "language_code": "ka",
                                                            "language_name": "georgian"
                                                        },
                                                        {
                                                            "language_code": "de",
                                                            "language_name": "german"
                                                        },
                                                        {
                                                            "language_code": "el",
                                                            "language_name": "greek"
                                                        },
                                                        {
                                                            "language_code": "gu",
                                                            "language_name": "gujarati"
                                                        },
                                                        {
                                                            "language_code": "ht",
                                                            "language_name": "haitian, haitian creole"
                                                        },
                                                        {
                                                            "language_code": "ha",
                                                            "language_name": "hausa"
                                                        },
                                                        {
                                                            "language_code": "he",
                                                            "language_name": "hebrew"
                                                        },
                                                        {
                                                            "language_code": "hi",
                                                            "language_name": "hindi"
                                                        },
                                                        {
                                                            "language_code": "hu",
                                                            "language_name": "hungarian"
                                                        },
                                                        {
                                                            "language_code": "is",
                                                            "language_name": "icelandic"
                                                        },
                                                        {
                                                            "language_code": "id",
                                                            "language_name": "indonesian"
                                                        },
                                                        {
                                                            "language_code": "ga",
                                                            "language_name": "irish"
                                                        },
                                                        {
                                                            "language_code": "it",
                                                            "language_name": "italian"
                                                        },
                                                        {
                                                            "language_code": "ja",
                                                            "language_name": "japanese"
                                                        },
                                                        {
                                                            "language_code": "kn",
                                                            "language_name": "kannada"
                                                        },
                                                        {
                                                            "language_code": "kk",
                                                            "language_name": "kazakh"
                                                        },
                                                        {
                                                            "language_code": "ko",
                                                            "language_name": "korean"
                                                        },
                                                        {
                                                            "language_code": "lv",
                                                            "language_name": "latvian"
                                                        },
                                                        {
                                                            "language_code": "lt",
                                                            "language_name": "lithuanian"
                                                        },
                                                        {
                                                            "language_code": "mk",
                                                            "language_name": "macedonian"
                                                        },
                                                        {
                                                            "language_code": "ms",
                                                            "language_name": "malay"
                                                        },
                                                        {
                                                            "language_code": "ml",
                                                            "language_name": "malayalam"
                                                        },
                                                        {
                                                            "language_code": "mt",
                                                            "language_name": "maltese"
                                                        },
                                                        {
                                                            "language_code": "mr",
                                                            "language_name": "marathi"
                                                        },
                                                        {
                                                            "language_code": "mn",
                                                            "language_name": "mongolian"
                                                        },
                                                        {
                                                            "language_code": "no",
                                                            "language_name": "norwegian"
                                                        },
                                                        {
                                                            "language_code": "ps",
                                                            "language_name": "pashto"
                                                        },
                                                        {
                                                            "language_code": "pl",
                                                            "language_name": "polish"
                                                        },
                                                        {
                                                            "language_code": "pt",
                                                            "language_name": "portuguese"
                                                        },
                                                        {
                                                            "language_code": "pa",
                                                            "language_name": "punjabi"
                                                        },
                                                        {
                                                            "language_code": "ro",
                                                            "language_name": "romanian"
                                                        },
                                                        {
                                                            "language_code": "ru",
                                                            "language_name": "russian"
                                                        },
                                                        {
                                                            "language_code": "sr",
                                                            "language_name": "serbian"
                                                        },
                                                        {
                                                            "language_code": "si",
                                                            "language_name": "sinhala"
                                                        },
                                                        {
                                                            "language_code": "sk",
                                                            "language_name": "slovak"
                                                        },
                                                        {
                                                            "language_code": "sl",
                                                            "language_name": "slovenian"
                                                        },
                                                        {
                                                            "language_code": "so",
                                                            "language_name": "somali"
                                                        },
                                                        {
                                                            "language_code": "es",
                                                            "language_name": "spanish"
                                                        },
                                                        {
                                                            "language_code": "sw",
                                                            "language_name": "swahili"
                                                        },
                                                        {
                                                            "language_code": "sv",
                                                            "language_name": "swedish"
                                                        },
                                                        {
                                                            "language_code": "ta",
                                                            "language_name": "tamil"
                                                        },
                                                        {
                                                            "language_code": "te",
                                                            "language_name": "telugu"
                                                        },
                                                        {
                                                            "language_code": "th",
                                                            "language_name": "thai"
                                                        },
                                                        {
                                                            "language_code": "tr",
                                                            "language_name": "turkish"
                                                        },
                                                        {
                                                            "language_code": "uk",
                                                            "language_name": "ukrainian"
                                                        },
                                                        {
                                                            "language_code": "ur",
                                                            "language_name": "urdu"
                                                        },
                                                        {
                                                            "language_code": "uz",
                                                            "language_name": "uzbek"
                                                        },
                                                        {
                                                            "language_code": "vi",
                                                            "language_name": "vietnamese"
                                                        },
                                                        {
                                                            "language_code": "cy",
                                                            "language_name": "welsh"
                                                        }
                                                    ]
                                                },
                                                {
                                                    "name": "deepl",
                                                    "display_name": "DeepL",
                                                    "description": "DeepL provides machine translation using neural networks, known for its high accuracy and fluency compared to other translation services.",
                                                    "pricing": "Pay-per-character",
                                                    "reliability": "high",
                                                    "price": 0.00162,
                                                    "languages_supported": [
                                                        {
                                                            "language_code": "bg",
                                                            "language_name": "bulgarian"
                                                        },
                                                        {
                                                            "language_code": "zh",
                                                            "language_name": "chinese"
                                                        },
                                                        {
                                                            "language_code": "cs",
                                                            "language_name": "czech"
                                                        },
                                                        {
                                                            "language_code": "da",
                                                            "language_name": "danish"
                                                        },
                                                        {
                                                            "language_code": "nl",
                                                            "language_name": "dutch"
                                                        },
                                                        {
                                                            "language_code": "en",
                                                            "language_name": "english"
                                                        },
                                                        {
                                                            "language_code": "et",
                                                            "language_name": "estonian"
                                                        },
                                                        {
                                                            "language_code": "fi",
                                                            "language_name": "finnish"
                                                        },
                                                        {
                                                            "language_code": "fr",
                                                            "language_name": "french"
                                                        },
                                                        {
                                                            "language_code": "de",
                                                            "language_name": "german"
                                                        },
                                                        {
                                                            "language_code": "el",
                                                            "language_name": "greek"
                                                        },
                                                        {
                                                            "language_code": "hu",
                                                            "language_name": "hungarian"
                                                        },
                                                        {
                                                            "language_code": "id",
                                                            "language_name": "indonesian"
                                                        },
                                                        {
                                                            "language_code": "it",
                                                            "language_name": "italian"
                                                        },
                                                        {
                                                            "language_code": "ja",
                                                            "language_name": "japanese"
                                                        },
                                                        {
                                                            "language_code": "ko",
                                                            "language_name": "korean"
                                                        },
                                                        {
                                                            "language_code": "lv",
                                                            "language_name": "latvian"
                                                        },
                                                        {
                                                            "language_code": "lt",
                                                            "language_name": "lithuanian"
                                                        },
                                                        {
                                                            "language_code": "no",
                                                            "language_name": "norwegian"
                                                        },
                                                        {
                                                            "language_code": "pl",
                                                            "language_name": "polish"
                                                        },
                                                        {
                                                            "language_code": "pt",
                                                            "language_name": "portuguese"
                                                        },
                                                        {
                                                            "language_code": "ro",
                                                            "language_name": "romanian"
                                                        },
                                                        {
                                                            "language_code": "ru",
                                                            "language_name": "russian"
                                                        },
                                                        {
                                                            "language_code": "sk",
                                                            "language_name": "slovak"
                                                        },
                                                        {
                                                            "language_code": "sl",
                                                            "language_name": "slovenian"
                                                        },
                                                        {
                                                            "language_code": "es",
                                                            "language_name": "spanish"
                                                        },
                                                        {
                                                            "language_code": "sv",
                                                            "language_name": "swedish"
                                                        },
                                                        {
                                                            "language_code": "tr",
                                                            "language_name": "turkish"
                                                        },
                                                        {
                                                            "language_code": "uk",
                                                            "language_name": "ukrainian"
                                                        },
                                                        {
                                                            "language_code": "ja",
                                                            "language_name": "japanese"
                                                        }
                                                    ]
                                                },
                                                {
                                                    "name": "deepl2",
                                                    "display_name": "DeepL2",
                                                    "description": "Like the original DeepL, but the parsing of subtitles is done by DeepL themself.",
                                                    "pricing": "Pay-per-character",
                                                    "reliability": "high",
                                                    "price": 0.00162,
                                                    "languages_supported": [
                                                        {
                                                            "language_code": "bg",
                                                            "language_name": "bulgarian"
                                                        },
                                                        {
                                                            "language_code": "zh",
                                                            "language_name": "chinese"
                                                        },
                                                        {
                                                            "language_code": "cs",
                                                            "language_name": "czech"
                                                        },
                                                        {
                                                            "language_code": "da",
                                                            "language_name": "danish"
                                                        },
                                                        {
                                                            "language_code": "nl",
                                                            "language_name": "dutch"
                                                        },
                                                        {
                                                            "language_code": "en",
                                                            "language_name": "english"
                                                        },
                                                        {
                                                            "language_code": "et",
                                                            "language_name": "estonian"
                                                        },
                                                        {
                                                            "language_code": "fi",
                                                            "language_name": "finnish"
                                                        },
                                                        {
                                                            "language_code": "fr",
                                                            "language_name": "french"
                                                        },
                                                        {
                                                            "language_code": "de",
                                                            "language_name": "german"
                                                        },
                                                        {
                                                            "language_code": "el",
                                                            "language_name": "greek"
                                                        },
                                                        {
                                                            "language_code": "hu",
                                                            "language_name": "hungarian"
                                                        },
                                                        {
                                                            "language_code": "id",
                                                            "language_name": "indonesian"
                                                        },
                                                        {
                                                            "language_code": "it",
                                                            "language_name": "italian"
                                                        },
                                                        {
                                                            "language_code": "ja",
                                                            "language_name": "japanese"
                                                        },
                                                        {
                                                            "language_code": "ko",
                                                            "language_name": "korean"
                                                        },
                                                        {
                                                            "language_code": "lv",
                                                            "language_name": "latvian"
                                                        },
                                                        {
                                                            "language_code": "lt",
                                                            "language_name": "lithuanian"
                                                        },
                                                        {
                                                            "language_code": "no",
                                                            "language_name": "norwegian"
                                                        },
                                                        {
                                                            "language_code": "pl",
                                                            "language_name": "polish"
                                                        },
                                                        {
                                                            "language_code": "pt",
                                                            "language_name": "portuguese"
                                                        },
                                                        {
                                                            "language_code": "ro",
                                                            "language_name": "romanian"
                                                        },
                                                        {
                                                            "language_code": "ru",
                                                            "language_name": "russian"
                                                        },
                                                        {
                                                            "language_code": "sk",
                                                            "language_name": "slovak"
                                                        },
                                                        {
                                                            "language_code": "sl",
                                                            "language_name": "slovenian"
                                                        },
                                                        {
                                                            "language_code": "es",
                                                            "language_name": "spanish"
                                                        },
                                                        {
                                                            "language_code": "sv",
                                                            "language_name": "swedish"
                                                        },
                                                        {
                                                            "language_code": "tr",
                                                            "language_name": "turkish"
                                                        },
                                                        {
                                                            "language_code": "uk",
                                                            "language_name": "ukrainian"
                                                        },
                                                        {
                                                            "language_code": "ja",
                                                            "language_name": "japanese"
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    }
                                },
                                "examples": {
                                    "Example 1": {
                                        "value": {
                                            "data": [
                                                {
                                                    "name": "aws",
                                                    "display_name": "Amazon Translate",
                                                    "description": "Neural machine translation by Amazon Web Service with support for many languages.",
                                                    "pricing": "Pay-per-character",
                                                    "reliability": "high",
                                                    "price": 0.0054,
                                                    "languages_supported": [
                                                        {
                                                            "language_code": "af",
                                                            "language_name": "afrikaans"
                                                        },
                                                        {
                                                            "language_code": "sq",
                                                            "language_name": "albanian"
                                                        },
                                                        {
                                                            "language_code": "am",
                                                            "language_name": "amharic"
                                                        },
                                                        {
                                                            "language_code": "ar",
                                                            "language_name": "arabic"
                                                        },
                                                        {
                                                            "language_code": "hy",
                                                            "language_name": "armenian"
                                                        },
                                                        {
                                                            "language_code": "az",
                                                            "language_name": "azerbaijani"
                                                        },
                                                        {
                                                            "language_code": "bn",
                                                            "language_name": "bengali"
                                                        },
                                                        {
                                                            "language_code": "bs",
                                                            "language_name": "bosnian"
                                                        },
                                                        {
                                                            "language_code": "bg",
                                                            "language_name": "bulgarian"
                                                        },
                                                        {
                                                            "language_code": "ca",
                                                            "language_name": "catalan"
                                                        },
                                                        {
                                                            "language_code": "zh",
                                                            "language_name": "chinese"
                                                        },
                                                        {
                                                            "language_code": "hr",
                                                            "language_name": "croatian"
                                                        },
                                                        {
                                                            "language_code": "cs",
                                                            "language_name": "czech"
                                                        },
                                                        {
                                                            "language_code": "da",
                                                            "language_name": "danish"
                                                        },
                                                        {
                                                            "language_code": "fa",
                                                            "language_name": "persian"
                                                        },
                                                        {
                                                            "language_code": "nl",
                                                            "language_name": "dutch"
                                                        },
                                                        {
                                                            "language_code": "en",
                                                            "language_name": "english"
                                                        },
                                                        {
                                                            "language_code": "et",
                                                            "language_name": "estonian"
                                                        },
                                                        {
                                                            "language_code": "tl",
                                                            "language_name": "tagalog"
                                                        },
                                                        {
                                                            "language_code": "fi",
                                                            "language_name": "finnish"
                                                        },
                                                        {
                                                            "language_code": "fr",
                                                            "language_name": "french"
                                                        },
                                                        {
                                                            "language_code": "fr-CA",
                                                            "language_name": "french (Canada)"
                                                        },
                                                        {
                                                            "language_code": "ka",
                                                            "language_name": "georgian"
                                                        },
                                                        {
                                                            "language_code": "de",
                                                            "language_name": "german"
                                                        },
                                                        {
                                                            "language_code": "el",
                                                            "language_name": "greek"
                                                        },
                                                        {
                                                            "language_code": "gu",
                                                            "language_name": "gujarati"
                                                        },
                                                        {
                                                            "language_code": "ht",
                                                            "language_name": "haitian, haitian creole"
                                                        },
                                                        {
                                                            "language_code": "ha",
                                                            "language_name": "hausa"
                                                        },
                                                        {
                                                            "language_code": "he",
                                                            "language_name": "hebrew"
                                                        },
                                                        {
                                                            "language_code": "hi",
                                                            "language_name": "hindi"
                                                        },
                                                        {
                                                            "language_code": "hu",
                                                            "language_name": "hungarian"
                                                        },
                                                        {
                                                            "language_code": "is",
                                                            "language_name": "icelandic"
                                                        },
                                                        {
                                                            "language_code": "id",
                                                            "language_name": "indonesian"
                                                        },
                                                        {
                                                            "language_code": "ga",
                                                            "language_name": "irish"
                                                        },
                                                        {
                                                            "language_code": "it",
                                                            "language_name": "italian"
                                                        },
                                                        {
                                                            "language_code": "ja",
                                                            "language_name": "japanese"
                                                        },
                                                        {
                                                            "language_code": "kn",
                                                            "language_name": "kannada"
                                                        },
                                                        {
                                                            "language_code": "kk",
                                                            "language_name": "kazakh"
                                                        },
                                                        {
                                                            "language_code": "ko",
                                                            "language_name": "korean"
                                                        },
                                                        {
                                                            "language_code": "lv",
                                                            "language_name": "latvian"
                                                        },
                                                        {
                                                            "language_code": "lt",
                                                            "language_name": "lithuanian"
                                                        },
                                                        {
                                                            "language_code": "mk",
                                                            "language_name": "macedonian"
                                                        },
                                                        {
                                                            "language_code": "ms",
                                                            "language_name": "malay"
                                                        },
                                                        {
                                                            "language_code": "ml",
                                                            "language_name": "malayalam"
                                                        },
                                                        {
                                                            "language_code": "mt",
                                                            "language_name": "maltese"
                                                        },
                                                        {
                                                            "language_code": "mr",
                                                            "language_name": "marathi"
                                                        },
                                                        {
                                                            "language_code": "mn",
                                                            "language_name": "mongolian"
                                                        },
                                                        {
                                                            "language_code": "no",
                                                            "language_name": "norwegian"
                                                        },
                                                        {
                                                            "language_code": "ps",
                                                            "language_name": "pashto"
                                                        },
                                                        {
                                                            "language_code": "pl",
                                                            "language_name": "polish"
                                                        },
                                                        {
                                                            "language_code": "pt",
                                                            "language_name": "portuguese"
                                                        },
                                                        {
                                                            "language_code": "pa",
                                                            "language_name": "punjabi"
                                                        },
                                                        {
                                                            "language_code": "ro",
                                                            "language_name": "romanian"
                                                        },
                                                        {
                                                            "language_code": "ru",
                                                            "language_name": "russian"
                                                        },
                                                        {
                                                            "language_code": "sr",
                                                            "language_name": "serbian"
                                                        },
                                                        {
                                                            "language_code": "si",
                                                            "language_name": "sinhala"
                                                        },
                                                        {
                                                            "language_code": "sk",
                                                            "language_name": "slovak"
                                                        },
                                                        {
                                                            "language_code": "sl",
                                                            "language_name": "slovenian"
                                                        },
                                                        {
                                                            "language_code": "so",
                                                            "language_name": "somali"
                                                        },
                                                        {
                                                            "language_code": "es",
                                                            "language_name": "spanish"
                                                        },
                                                        {
                                                            "language_code": "sw",
                                                            "language_name": "swahili"
                                                        },
                                                        {
                                                            "language_code": "sv",
                                                            "language_name": "swedish"
                                                        },
                                                        {
                                                            "language_code": "ta",
                                                            "language_name": "tamil"
                                                        },
                                                        {
                                                            "language_code": "te",
                                                            "language_name": "telugu"
                                                        },
                                                        {
                                                            "language_code": "th",
                                                            "language_name": "thai"
                                                        },
                                                        {
                                                            "language_code": "tr",
                                                            "language_name": "turkish"
                                                        },
                                                        {
                                                            "language_code": "uk",
                                                            "language_name": "ukrainian"
                                                        },
                                                        {
                                                            "language_code": "ur",
                                                            "language_name": "urdu"
                                                        },
                                                        {
                                                            "language_code": "uz",
                                                            "language_name": "uzbek"
                                                        },
                                                        {
                                                            "language_code": "vi",
                                                            "language_name": "vietnamese"
                                                        },
                                                        {
                                                            "language_code": "cy",
                                                            "language_name": "welsh"
                                                        }
                                                    ]
                                                },
                                                {
                                                    "name": "deepl",
                                                    "display_name": "DeepL",
                                                    "description": "DeepL provides machine translation using neural networks, known for its high accuracy and fluency compared to other translation services.",
                                                    "pricing": "Pay-per-character",
                                                    "reliability": "high",
                                                    "price": 0.00162,
                                                    "languages_supported": [
                                                        {
                                                            "language_code": "bg",
                                                            "language_name": "bulgarian"
                                                        },
                                                        {
                                                            "language_code": "zh",
                                                            "language_name": "chinese"
                                                        },
                                                        {
                                                            "language_code": "cs",
                                                            "language_name": "czech"
                                                        },
                                                        {
                                                            "language_code": "da",
                                                            "language_name": "danish"
                                                        },
                                                        {
                                                            "language_code": "nl",
                                                            "language_name": "dutch"
                                                        },
                                                        {
                                                            "language_code": "en",
                                                            "language_name": "english"
                                                        },
                                                        {
                                                            "language_code": "et",
                                                            "language_name": "estonian"
                                                        },
                                                        {
                                                            "language_code": "fi",
                                                            "language_name": "finnish"
                                                        },
                                                        {
                                                            "language_code": "fr",
                                                            "language_name": "french"
                                                        },
                                                        {
                                                            "language_code": "de",
                                                            "language_name": "german"
                                                        },
                                                        {
                                                            "language_code": "el",
                                                            "language_name": "greek"
                                                        },
                                                        {
                                                            "language_code": "hu",
                                                            "language_name": "hungarian"
                                                        },
                                                        {
                                                            "language_code": "id",
                                                            "language_name": "indonesian"
                                                        },
                                                        {
                                                            "language_code": "it",
                                                            "language_name": "italian"
                                                        },
                                                        {
                                                            "language_code": "ja",
                                                            "language_name": "japanese"
                                                        },
                                                        {
                                                            "language_code": "ko",
                                                            "language_name": "korean"
                                                        },
                                                        {
                                                            "language_code": "lv",
                                                            "language_name": "latvian"
                                                        },
                                                        {
                                                            "language_code": "lt",
                                                            "language_name": "lithuanian"
                                                        },
                                                        {
                                                            "language_code": "no",
                                                            "language_name": "norwegian"
                                                        },
                                                        {
                                                            "language_code": "pl",
                                                            "language_name": "polish"
                                                        },
                                                        {
                                                            "language_code": "pt",
                                                            "language_name": "portuguese"
                                                        },
                                                        {
                                                            "language_code": "ro",
                                                            "language_name": "romanian"
                                                        },
                                                        {
                                                            "language_code": "ru",
                                                            "language_name": "russian"
                                                        },
                                                        {
                                                            "language_code": "sk",
                                                            "language_name": "slovak"
                                                        },
                                                        {
                                                            "language_code": "sl",
                                                            "language_name": "slovenian"
                                                        },
                                                        {
                                                            "language_code": "es",
                                                            "language_name": "spanish"
                                                        },
                                                        {
                                                            "language_code": "sv",
                                                            "language_name": "swedish"
                                                        },
                                                        {
                                                            "language_code": "tr",
                                                            "language_name": "turkish"
                                                        },
                                                        {
                                                            "language_code": "uk",
                                                            "language_name": "ukrainian"
                                                        },
                                                        {
                                                            "language_code": "ja",
                                                            "language_name": "japanese"
                                                        }
                                                    ]
                                                },
                                                {
                                                    "name": "deepl2",
                                                    "display_name": "DeepL2",
                                                    "description": "Like the original DeepL, but the parsing of subtitles is done by DeepL themself.",
                                                    "pricing": "Pay-per-character",
                                                    "reliability": "high",
                                                    "price": 0.00162,
                                                    "languages_supported": [
                                                        {
                                                            "language_code": "bg",
                                                            "language_name": "bulgarian"
                                                        },
                                                        {
                                                            "language_code": "zh",
                                                            "language_name": "chinese"
                                                        },
                                                        {
                                                            "language_code": "cs",
                                                            "language_name": "czech"
                                                        },
                                                        {
                                                            "language_code": "da",
                                                            "language_name": "danish"
                                                        },
                                                        {
                                                            "language_code": "nl",
                                                            "language_name": "dutch"
                                                        },
                                                        {
                                                            "language_code": "en",
                                                            "language_name": "english"
                                                        },
                                                        {
                                                            "language_code": "et",
                                                            "language_name": "estonian"
                                                        },
                                                        {
                                                            "language_code": "fi",
                                                            "language_name": "finnish"
                                                        },
                                                        {
                                                            "language_code": "fr",
                                                            "language_name": "french"
                                                        },
                                                        {
                                                            "language_code": "de",
                                                            "language_name": "german"
                                                        },
                                                        {
                                                            "language_code": "el",
                                                            "language_name": "greek"
                                                        },
                                                        {
                                                            "language_code": "hu",
                                                            "language_name": "hungarian"
                                                        },
                                                        {
                                                            "language_code": "id",
                                                            "language_name": "indonesian"
                                                        },
                                                        {
                                                            "language_code": "it",
                                                            "language_name": "italian"
                                                        },
                                                        {
                                                            "language_code": "ja",
                                                            "language_name": "japanese"
                                                        },
                                                        {
                                                            "language_code": "ko",
                                                            "language_name": "korean"
                                                        },
                                                        {
                                                            "language_code": "lv",
                                                            "language_name": "latvian"
                                                        },
                                                        {
                                                            "language_code": "lt",
                                                            "language_name": "lithuanian"
                                                        },
                                                        {
                                                            "language_code": "no",
                                                            "language_name": "norwegian"
                                                        },
                                                        {
                                                            "language_code": "pl",
                                                            "language_name": "polish"
                                                        },
                                                        {
                                                            "language_code": "pt",
                                                            "language_name": "portuguese"
                                                        },
                                                        {
                                                            "language_code": "ro",
                                                            "language_name": "romanian"
                                                        },
                                                        {
                                                            "language_code": "ru",
                                                            "language_name": "russian"
                                                        },
                                                        {
                                                            "language_code": "sk",
                                                            "language_name": "slovak"
                                                        },
                                                        {
                                                            "language_code": "sl",
                                                            "language_name": "slovenian"
                                                        },
                                                        {
                                                            "language_code": "es",
                                                            "language_name": "spanish"
                                                        },
                                                        {
                                                            "language_code": "sv",
                                                            "language_name": "swedish"
                                                        },
                                                        {
                                                            "language_code": "tr",
                                                            "language_name": "turkish"
                                                        },
                                                        {
                                                            "language_code": "uk",
                                                            "language_name": "ukrainian"
                                                        },
                                                        {
                                                            "language_code": "ja",
                                                            "language_name": "japanese"
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "operationId": "translation",
                "description": "Available translation APIs and Languages. User doesn't need to be authentificated.\n\n",
                "parameters": [
                    {
                        "schema": {
                            "type": "string"
                        },
                        "in": "header",
                        "name": "User-Agent",
                        "description": "<<{{APP_NAME}} v{{APP_VERSION}}>>"
                    }
                ],
                "x-internal": false,
                "x-stoplight": {
                    "id": "5lfbmcs2cnuk9"
                },
                "security": [
                    {
                        "Api-Key": []
                    }
                ]
            },
            "parameters": []
        },
        "/ai/translate": {
            "post": {
                "summary": "AI Translate",
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {
                            "multipart/form-data": {
                                "schema": {
                                    "type": "object",
                                    "properties": {}
                                }
                            }
                        }
                    }
                },
                "operationId": "translate",
                "x-stoplight": {
                    "id": "jeeb1raxhoz3r"
                },
                "description": "**Translate** subtitles using AI from one language to another language. \n\nCredits on user account are needed. [Buy Credits](../open_api.json/paths/~1ai~1credits~1buy/get)\n\nCheck following method: [Get AI Translate status](../open_api.json/paths/~1ai~1translate~1{correlation_id}/get)\n\nMethod is returning \n```\n{\n  \"status\": \"CREATED\",\n  \"correlation_id\": \"67eda18f52e11\"\n}\n```\nStatus possible values: \n```\nCREATED     -> Initial state`\nPENDING     -> procedure is still running\nCOMPLETED   -> remote procedure call is completed and has a result\nERROR       -> procedure resulted in an error and is not running anymore\nTIMEOUT     -> No matching procedure call found before timeout\n```\nUsing `correlation_id` can check status of job using GET\n",
                "security": [
                    {
                        "Api-Key": []
                    },
                    {
                        "Bearer": []
                    }
                ],
                "parameters": [
                    {
                        "schema": {
                            "type": "string"
                        },
                        "in": "query",
                        "name": "api",
                        "description": "translation_apis",
                        "required": true
                    },
                    {
                        "schema": {
                            "type": "string"
                        },
                        "in": "query",
                        "name": "file",
                        "description": "file contents to translate",
                        "required": true
                    },
                    {
                        "schema": {
                            "type": "string",
                            "default": "auto"
                        },
                        "in": "query",
                        "name": "translate_from",
                        "description": "language ISO639 translate_from (auto is default)"
                    },
                    {
                        "schema": {
                            "type": "string"
                        },
                        "in": "query",
                        "name": "translate_to",
                        "description": "language ISO639 translate_from",
                        "required": true
                    },
                    {
                        "schema": {
                            "type": "integer"
                        },
                        "in": "query",
                        "name": "file_id",
                        "description": "file_id from /subtitles endpoint"
                    }
                ],
                "tags": [
                    "AI Translate"
                ]
            },
            "parameters": []
        },
        "/ai/translate/{correlation_id}": {
            "get": {
                "summary": "AI Translate status",
                "responses": {
                    "200": {
                        "description": "OK"
                    }
                },
                "operationId": "translate-status",
                "x-stoplight": {
                    "id": "wxehdpdtbozcf"
                },
                "security": [
                    {
                        "Api-Key": []
                    },
                    {
                        "Bearer": []
                    }
                ],
                "description": "Get status of **[translate](..open_api.json/paths/~1ai~1translate/post)** job using `correlation_id`\n",
                "tags": [
                    "AI Translate"
                ]
            },
            "parameters": [
                {
                    "schema": {
                        "type": "string"
                    },
                    "name": "correlation_id",
                    "in": "path",
                    "required": true,
                    "description": "correlation_id"
                }
            ]
        },
        "/ai/info/transcription": {
            "parameters": [],
            "get": {
                "summary": "AI Transcription",
                "tags": [
                    "Infos"
                ],
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "data": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "name": {
                                                        "type": "string"
                                                    },
                                                    "display_name": {
                                                        "type": "string"
                                                    },
                                                    "description": {
                                                        "type": "string"
                                                    },
                                                    "pricing": {
                                                        "type": "string"
                                                    },
                                                    "reliability": {
                                                        "type": "string"
                                                    },
                                                    "price": {
                                                        "type": "number"
                                                    },
                                                    "languages_supported": {
                                                        "type": "array",
                                                        "items": {
                                                            "type": "object",
                                                            "properties": {
                                                                "language_code": {
                                                                    "type": "string"
                                                                },
                                                                "language_name": {
                                                                    "type": "string"
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    "x-examples": {
                                        "Example 1": {
                                            "data": [
                                                {
                                                    "name": "aws",
                                                    "display_name": "Amazon Transcribe",
                                                    "description": "Neural machine transcription by Amazon Web Service with suport for many languages for a premium price/",
                                                    "pricing": "Pay-per-second",
                                                    "reliability": "high",
                                                    "price": 0.132,
                                                    "languages_supported": [
                                                        {
                                                            "language_code": "auto",
                                                            "language_name": "automatic selection"
                                                        },
                                                        {
                                                            "language_code": "en",
                                                            "language_name": "english"
                                                        },
                                                        {
                                                            "language_code": "ab-GE",
                                                            "language_name": "abkhaz"
                                                        },
                                                        {
                                                            "language_code": "af-ZA",
                                                            "language_name": "afrikaans (South Africa)"
                                                        },
                                                        {
                                                            "language_code": "ar-AE",
                                                            "language_name": "arabic (United Arab Emirates)"
                                                        },
                                                        {
                                                            "language_code": "ar-SA",
                                                            "language_name": "arabic (Saudi Arabia)"
                                                        },
                                                        {
                                                            "language_code": "hy-AM",
                                                            "language_name": "armenian (Armenia)"
                                                        },
                                                        {
                                                            "language_code": "ast-ES",
                                                            "language_name": "ast-ES"
                                                        },
                                                        {
                                                            "language_code": "az-AZ",
                                                            "language_name": "azerbaijani (Azerbaijan)"
                                                        },
                                                        {
                                                            "language_code": "ba-RU",
                                                            "language_name": "bashkir"
                                                        },
                                                        {
                                                            "language_code": "eu-ES",
                                                            "language_name": "basque (Spain)"
                                                        },
                                                        {
                                                            "language_code": "be-BY",
                                                            "language_name": "belarusian (Belarus)"
                                                        },
                                                        {
                                                            "language_code": "bn-IN",
                                                            "language_name": "bengali (India)"
                                                        },
                                                        {
                                                            "language_code": "bs-BA",
                                                            "language_name": "bosnian (Bosnia and Herzegovina)"
                                                        },
                                                        {
                                                            "language_code": "bg-BG",
                                                            "language_name": "bulgarian (Bulgaria)"
                                                        },
                                                        {
                                                            "language_code": "ca-ES",
                                                            "language_name": "catalan (Spain)"
                                                        },
                                                        {
                                                            "language_code": "ckb-IR",
                                                            "language_name": "ckb-IR"
                                                        },
                                                        {
                                                            "language_code": "ckb-IQ",
                                                            "language_name": "ckb-IQ"
                                                        },
                                                        {
                                                            "language_code": "zh-CN",
                                                            "language_name": "chinese (China)"
                                                        },
                                                        {
                                                            "language_code": "zh-TW",
                                                            "language_name": "chinese (Taiwan)"
                                                        },
                                                        {
                                                            "language_code": "hr-HR",
                                                            "language_name": "croatian (Croatia)"
                                                        },
                                                        {
                                                            "language_code": "cs-CZ",
                                                            "language_name": "czech (Czech Republic)"
                                                        },
                                                        {
                                                            "language_code": "da-DK",
                                                            "language_name": "danish (Denmark)"
                                                        },
                                                        {
                                                            "language_code": "nl-NL",
                                                            "language_name": "dutch (Netherlands)"
                                                        },
                                                        {
                                                            "language_code": "en-AU",
                                                            "language_name": "english (Australia)"
                                                        },
                                                        {
                                                            "language_code": "en-GB",
                                                            "language_name": "english (United Kingdom)"
                                                        },
                                                        {
                                                            "language_code": "en-IN",
                                                            "language_name": "english (India)"
                                                        },
                                                        {
                                                            "language_code": "en-IE",
                                                            "language_name": "english (Ireland)"
                                                        },
                                                        {
                                                            "language_code": "en-NZ",
                                                            "language_name": "english (New Zealand)"
                                                        },
                                                        {
                                                            "language_code": "en-AB",
                                                            "language_name": "english"
                                                        },
                                                        {
                                                            "language_code": "en-ZA",
                                                            "language_name": "english (South Africa)"
                                                        },
                                                        {
                                                            "language_code": "en-US",
                                                            "language_name": "english (United States)"
                                                        },
                                                        {
                                                            "language_code": "en-WL",
                                                            "language_name": "english"
                                                        },
                                                        {
                                                            "language_code": "et-ET",
                                                            "language_name": "estonian"
                                                        },
                                                        {
                                                            "language_code": "fa-IR",
                                                            "language_name": "persian (Iran)"
                                                        },
                                                        {
                                                            "language_code": "fi-FI",
                                                            "language_name": "finnish (Finland)"
                                                        },
                                                        {
                                                            "language_code": "fr-FR",
                                                            "language_name": "french (France)"
                                                        },
                                                        {
                                                            "language_code": "fr-CA",
                                                            "language_name": "french (Canada)"
                                                        },
                                                        {
                                                            "language_code": "gl-ES",
                                                            "language_name": "galician (Spain)"
                                                        },
                                                        {
                                                            "language_code": "ka-GE",
                                                            "language_name": "georgian (Georgia)"
                                                        },
                                                        {
                                                            "language_code": "de-DE",
                                                            "language_name": "german (Germany)"
                                                        },
                                                        {
                                                            "language_code": "de-CH",
                                                            "language_name": "german (Switzerland)"
                                                        },
                                                        {
                                                            "language_code": "el-GR",
                                                            "language_name": "greek (Greece)"
                                                        },
                                                        {
                                                            "language_code": "gu-IN",
                                                            "language_name": "gujarati (India)"
                                                        },
                                                        {
                                                            "language_code": "ha-NG",
                                                            "language_name": "hausa (Nigeria)"
                                                        },
                                                        {
                                                            "language_code": "he-IL",
                                                            "language_name": "hebrew (Israel)"
                                                        },
                                                        {
                                                            "language_code": "hi-IN",
                                                            "language_name": "hindi (India)"
                                                        },
                                                        {
                                                            "language_code": "hu-HU",
                                                            "language_name": "hungarian (Hungary)"
                                                        },
                                                        {
                                                            "language_code": "is-IS",
                                                            "language_name": "icelandic (Iceland)"
                                                        },
                                                        {
                                                            "language_code": "id-ID",
                                                            "language_name": "indonesian (Indonesia)"
                                                        },
                                                        {
                                                            "language_code": "it-IT",
                                                            "language_name": "italian (Italy)"
                                                        },
                                                        {
                                                            "language_code": "ja-JP",
                                                            "language_name": "japanese (Japan)"
                                                        },
                                                        {
                                                            "language_code": "kab-DZ",
                                                            "language_name": "kabyle (Algeria)"
                                                        },
                                                        {
                                                            "language_code": "kn-IN",
                                                            "language_name": "kannada (India)"
                                                        },
                                                        {
                                                            "language_code": "kk-KZ",
                                                            "language_name": "kazakh (Kazakhstan)"
                                                        },
                                                        {
                                                            "language_code": "rw-RW",
                                                            "language_name": "kinyarwanda (Rwanda)"
                                                        },
                                                        {
                                                            "language_code": "ko-KR",
                                                            "language_name": "korean (South Korea)"
                                                        },
                                                        {
                                                            "language_code": "ky-KG",
                                                            "language_name": "kyrgyz"
                                                        },
                                                        {
                                                            "language_code": "lv-LV",
                                                            "language_name": "latvian (Latvia)"
                                                        },
                                                        {
                                                            "language_code": "lt-LT",
                                                            "language_name": "lithuanian (Lithuania)"
                                                        },
                                                        {
                                                            "language_code": "lg-IN",
                                                            "language_name": "ganda"
                                                        },
                                                        {
                                                            "language_code": "mk-MK",
                                                            "language_name": "macedonian (Macedonia)"
                                                        },
                                                        {
                                                            "language_code": "ms-MY",
                                                            "language_name": "malay (Malaysia)"
                                                        },
                                                        {
                                                            "language_code": "ml-IN",
                                                            "language_name": "malayalam (India)"
                                                        },
                                                        {
                                                            "language_code": "mt-MT",
                                                            "language_name": "maltese (Malta)"
                                                        },
                                                        {
                                                            "language_code": "mr-IN",
                                                            "language_name": "marathi (India)"
                                                        },
                                                        {
                                                            "language_code": "mhr-RU",
                                                            "language_name": "mhr-RU"
                                                        },
                                                        {
                                                            "language_code": "mn-MN",
                                                            "language_name": "mongolian"
                                                        },
                                                        {
                                                            "language_code": "no-NO",
                                                            "language_name": "norwegian"
                                                        },
                                                        {
                                                            "language_code": "or-IN",
                                                            "language_name": "oriya (India)"
                                                        },
                                                        {
                                                            "language_code": "ps-AF",
                                                            "language_name": "pashto (Afghanistan)"
                                                        },
                                                        {
                                                            "language_code": "pl-PL",
                                                            "language_name": "polish (Poland)"
                                                        },
                                                        {
                                                            "language_code": "pt-PT",
                                                            "language_name": "portuguese (Portugal)"
                                                        },
                                                        {
                                                            "language_code": "pt-BR",
                                                            "language_name": "portuguese (Brazil)"
                                                        },
                                                        {
                                                            "language_code": "pa-IN",
                                                            "language_name": "punjabi (India)"
                                                        },
                                                        {
                                                            "language_code": "ro-RO",
                                                            "language_name": "romanian (Romania)"
                                                        },
                                                        {
                                                            "language_code": "ru-RU",
                                                            "language_name": "russian (Russia)"
                                                        },
                                                        {
                                                            "language_code": "sr-RS",
                                                            "language_name": "serbian (Serbia)"
                                                        },
                                                        {
                                                            "language_code": "si-LK",
                                                            "language_name": "sinhala (Sri Lanka)"
                                                        },
                                                        {
                                                            "language_code": "sk-SK",
                                                            "language_name": "slovak (Slovakia)"
                                                        },
                                                        {
                                                            "language_code": "sl-SI",
                                                            "language_name": "slovenian (Slovenia)"
                                                        },
                                                        {
                                                            "language_code": "so-SO",
                                                            "language_name": "somali (Somalia)"
                                                        },
                                                        {
                                                            "language_code": "es-ES",
                                                            "language_name": "spanish (Spain)"
                                                        },
                                                        {
                                                            "language_code": "es-US",
                                                            "language_name": "spanish (United States)"
                                                        },
                                                        {
                                                            "language_code": "su-ID",
                                                            "language_name": "sundanese"
                                                        },
                                                        {
                                                            "language_code": "sw-KE",
                                                            "language_name": "swahili (Kenya)"
                                                        },
                                                        {
                                                            "language_code": "sw-BI",
                                                            "language_name": "swahili"
                                                        },
                                                        {
                                                            "language_code": "sw-RW",
                                                            "language_name": "swahili"
                                                        },
                                                        {
                                                            "language_code": "sw-TZ",
                                                            "language_name": "swahili (Tanzania)"
                                                        },
                                                        {
                                                            "language_code": "sw-UG",
                                                            "language_name": "swahili"
                                                        },
                                                        {
                                                            "language_code": "sv-SE",
                                                            "language_name": "swedish (Sweden)"
                                                        },
                                                        {
                                                            "language_code": "tl-PH",
                                                            "language_name": "tagalog"
                                                        },
                                                        {
                                                            "language_code": "ta-IN",
                                                            "language_name": "tamil (India)"
                                                        },
                                                        {
                                                            "language_code": "tt-RU",
                                                            "language_name": "tatar"
                                                        },
                                                        {
                                                            "language_code": "te-IN",
                                                            "language_name": "telugu (India)"
                                                        },
                                                        {
                                                            "language_code": "th-TH",
                                                            "language_name": "thai (Thailand)"
                                                        },
                                                        {
                                                            "language_code": "tr-TR",
                                                            "language_name": "turkish (Turkey)"
                                                        },
                                                        {
                                                            "language_code": "uk-UA",
                                                            "language_name": "ukrainian (Ukraine)"
                                                        },
                                                        {
                                                            "language_code": "ug-CN",
                                                            "language_name": "uyghur, uighur"
                                                        },
                                                        {
                                                            "language_code": "uz-UZ",
                                                            "language_name": "uzbek (Uzbekistan)"
                                                        },
                                                        {
                                                            "language_code": "vi-VN",
                                                            "language_name": "vietnamese (Vietnam)"
                                                        },
                                                        {
                                                            "language_code": "cy-WL",
                                                            "language_name": "welsh"
                                                        },
                                                        {
                                                            "language_code": "wo-SN",
                                                            "language_name": "wolof"
                                                        },
                                                        {
                                                            "language_code": "zu-ZA",
                                                            "language_name": "zulu (South Africa)"
                                                        }
                                                    ]
                                                },
                                                {
                                                    "name": "salad",
                                                    "display_name": "Salad Transcribe",
                                                    "description": "Salad’s Transcription API is based on OpenAI's Whiper model, offering low cost transcription",
                                                    "pricing": "Pay-per-second",
                                                    "reliability": "low",
                                                    "price": 0.0054,
                                                    "languages_supported": [
                                                        {
                                                            "language_code": "en",
                                                            "language_name": "english"
                                                        },
                                                        {
                                                            "language_code": "fr",
                                                            "language_name": "french"
                                                        },
                                                        {
                                                            "language_code": "de",
                                                            "language_name": "german"
                                                        },
                                                        {
                                                            "language_code": "es",
                                                            "language_name": "spanish"
                                                        },
                                                        {
                                                            "language_code": "it",
                                                            "language_name": "italian"
                                                        },
                                                        {
                                                            "language_code": "ja",
                                                            "language_name": "japanese"
                                                        },
                                                        {
                                                            "language_code": "zh",
                                                            "language_name": "chinese"
                                                        },
                                                        {
                                                            "language_code": "nl",
                                                            "language_name": "dutch"
                                                        },
                                                        {
                                                            "language_code": "uk",
                                                            "language_name": "ukrainian"
                                                        },
                                                        {
                                                            "language_code": "pt",
                                                            "language_name": "portuguese"
                                                        },
                                                        {
                                                            "language_code": "ar",
                                                            "language_name": "arabic"
                                                        },
                                                        {
                                                            "language_code": "cs",
                                                            "language_name": "czech"
                                                        },
                                                        {
                                                            "language_code": "ru",
                                                            "language_name": "russian"
                                                        },
                                                        {
                                                            "language_code": "pl",
                                                            "language_name": "polish"
                                                        },
                                                        {
                                                            "language_code": "hu",
                                                            "language_name": "hungarian"
                                                        },
                                                        {
                                                            "language_code": "fi",
                                                            "language_name": "finnish"
                                                        },
                                                        {
                                                            "language_code": "fa",
                                                            "language_name": "persian"
                                                        },
                                                        {
                                                            "language_code": "el",
                                                            "language_name": "greek"
                                                        },
                                                        {
                                                            "language_code": "tr",
                                                            "language_name": "turkish"
                                                        },
                                                        {
                                                            "language_code": "da",
                                                            "language_name": "danish"
                                                        },
                                                        {
                                                            "language_code": "he",
                                                            "language_name": "hebrew"
                                                        },
                                                        {
                                                            "language_code": "vi",
                                                            "language_name": "vietnamese"
                                                        },
                                                        {
                                                            "language_code": "ko",
                                                            "language_name": "korean"
                                                        },
                                                        {
                                                            "language_code": "ur",
                                                            "language_name": "urdu"
                                                        },
                                                        {
                                                            "language_code": "te",
                                                            "language_name": "telugu"
                                                        },
                                                        {
                                                            "language_code": "hi",
                                                            "language_name": "hindi"
                                                        },
                                                        {
                                                            "language_code": "ca",
                                                            "language_name": "catalan"
                                                        },
                                                        {
                                                            "language_code": "ml",
                                                            "language_name": "malayalam"
                                                        }
                                                    ]
                                                },
                                                {
                                                    "name": "openai",
                                                    "display_name": "OpenAI Whisper",
                                                    "description": "OpenAI's Whiper model, run by OpenAI",
                                                    "pricing": "Pay-per-second",
                                                    "reliability": "medium",
                                                    "price": 0.033,
                                                    "languages_supported": [
                                                        {
                                                            "language_code": "af-ZA",
                                                            "language_name": "afrikaans (South Africa)"
                                                        },
                                                        {
                                                            "language_code": "ar-SA",
                                                            "language_name": "arabic (Saudi Arabia)"
                                                        },
                                                        {
                                                            "language_code": "hy-AM",
                                                            "language_name": "armenian (Armenia)"
                                                        },
                                                        {
                                                            "language_code": "az-AZ",
                                                            "language_name": "azerbaijani (Azerbaijan)"
                                                        },
                                                        {
                                                            "language_code": "be-BY",
                                                            "language_name": "belarusian (Belarus)"
                                                        },
                                                        {
                                                            "language_code": "bs-BA",
                                                            "language_name": "bosnian (Bosnia and Herzegovina)"
                                                        },
                                                        {
                                                            "language_code": "bg-BG",
                                                            "language_name": "bulgarian (Bulgaria)"
                                                        },
                                                        {
                                                            "language_code": "ca-ES",
                                                            "language_name": "catalan (Spain)"
                                                        },
                                                        {
                                                            "language_code": "zh-CN",
                                                            "language_name": "chinese (China)"
                                                        },
                                                        {
                                                            "language_code": "hr-HR",
                                                            "language_name": "croatian (Croatia)"
                                                        },
                                                        {
                                                            "language_code": "cs-CZ",
                                                            "language_name": "czech (Czech Republic)"
                                                        },
                                                        {
                                                            "language_code": "da-DK",
                                                            "language_name": "danish (Denmark)"
                                                        },
                                                        {
                                                            "language_code": "nl-NL",
                                                            "language_name": "dutch (Netherlands)"
                                                        },
                                                        {
                                                            "language_code": "en",
                                                            "language_name": "english"
                                                        },
                                                        {
                                                            "language_code": "en-US",
                                                            "language_name": "english (United States)"
                                                        },
                                                        {
                                                            "language_code": "et-EE",
                                                            "language_name": "estonian (Estonia)"
                                                        },
                                                        {
                                                            "language_code": "fi-FI",
                                                            "language_name": "finnish (Finland)"
                                                        },
                                                        {
                                                            "language_code": "fr-FR",
                                                            "language_name": "french (France)"
                                                        },
                                                        {
                                                            "language_code": "gl-ES",
                                                            "language_name": "galician (Spain)"
                                                        },
                                                        {
                                                            "language_code": "de-DE",
                                                            "language_name": "german (Germany)"
                                                        },
                                                        {
                                                            "language_code": "el-GR",
                                                            "language_name": "greek (Greece)"
                                                        },
                                                        {
                                                            "language_code": "he-IL",
                                                            "language_name": "hebrew (Israel)"
                                                        },
                                                        {
                                                            "language_code": "hi-IN",
                                                            "language_name": "hindi (India)"
                                                        },
                                                        {
                                                            "language_code": "hu-HU",
                                                            "language_name": "hungarian (Hungary)"
                                                        },
                                                        {
                                                            "language_code": "is-IS",
                                                            "language_name": "icelandic (Iceland)"
                                                        },
                                                        {
                                                            "language_code": "id-ID",
                                                            "language_name": "indonesian (Indonesia)"
                                                        },
                                                        {
                                                            "language_code": "it-IT",
                                                            "language_name": "italian (Italy)"
                                                        },
                                                        {
                                                            "language_code": "ja-JP",
                                                            "language_name": "japanese (Japan)"
                                                        },
                                                        {
                                                            "language_code": "kn-IN",
                                                            "language_name": "kannada (India)"
                                                        },
                                                        {
                                                            "language_code": "kk-KZ",
                                                            "language_name": "kazakh (Kazakhstan)"
                                                        },
                                                        {
                                                            "language_code": "ko-KR",
                                                            "language_name": "korean (South Korea)"
                                                        },
                                                        {
                                                            "language_code": "lv-LV",
                                                            "language_name": "latvian (Latvia)"
                                                        },
                                                        {
                                                            "language_code": "lt-LT",
                                                            "language_name": "lithuanian (Lithuania)"
                                                        },
                                                        {
                                                            "language_code": "mk-MK",
                                                            "language_name": "macedonian (Macedonia)"
                                                        },
                                                        {
                                                            "language_code": "ms-MY",
                                                            "language_name": "malay (Malaysia)"
                                                        },
                                                        {
                                                            "language_code": "mr-IN",
                                                            "language_name": "marathi (India)"
                                                        },
                                                        {
                                                            "language_code": "mi-NZ",
                                                            "language_name": "māori"
                                                        },
                                                        {
                                                            "language_code": "ne-NP",
                                                            "language_name": "nepali (Nepal)"
                                                        },
                                                        {
                                                            "language_code": "nb-NO",
                                                            "language_name": "norwegian bokmål (Norway)"
                                                        },
                                                        {
                                                            "language_code": "fa-IR",
                                                            "language_name": "persian (Iran)"
                                                        },
                                                        {
                                                            "language_code": "pl-PL",
                                                            "language_name": "polish (Poland)"
                                                        },
                                                        {
                                                            "language_code": "pt-PT",
                                                            "language_name": "portuguese (Portugal)"
                                                        },
                                                        {
                                                            "language_code": "ro-RO",
                                                            "language_name": "romanian (Romania)"
                                                        },
                                                        {
                                                            "language_code": "ru-RU",
                                                            "language_name": "russian (Russia)"
                                                        },
                                                        {
                                                            "language_code": "sr-RS",
                                                            "language_name": "serbian (Serbia)"
                                                        },
                                                        {
                                                            "language_code": "sk-SK",
                                                            "language_name": "slovak (Slovakia)"
                                                        },
                                                        {
                                                            "language_code": "sl-SI",
                                                            "language_name": "slovenian (Slovenia)"
                                                        },
                                                        {
                                                            "language_code": "es-ES",
                                                            "language_name": "spanish (Spain)"
                                                        },
                                                        {
                                                            "language_code": "sw-KE",
                                                            "language_name": "swahili (Kenya)"
                                                        },
                                                        {
                                                            "language_code": "sv-SE",
                                                            "language_name": "swedish (Sweden)"
                                                        },
                                                        {
                                                            "language_code": "tl-PH",
                                                            "language_name": "tagalog"
                                                        },
                                                        {
                                                            "language_code": "ta-IN",
                                                            "language_name": "tamil (India)"
                                                        },
                                                        {
                                                            "language_code": "th-TH",
                                                            "language_name": "thai (Thailand)"
                                                        },
                                                        {
                                                            "language_code": "tr-TR",
                                                            "language_name": "turkish (Turkey)"
                                                        },
                                                        {
                                                            "language_code": "uk-UA",
                                                            "language_name": "ukrainian (Ukraine)"
                                                        },
                                                        {
                                                            "language_code": "ur-PK",
                                                            "language_name": "urdu (Pakistan)"
                                                        },
                                                        {
                                                            "language_code": "vi-VN",
                                                            "language_name": "vietnamese (Vietnam)"
                                                        },
                                                        {
                                                            "language_code": "cy-GB",
                                                            "language_name": "welsh (United Kingdom)"
                                                        }
                                                    ]
                                                },
                                                {
                                                    "name": "assemblyAI",
                                                    "display_name": "AssemblyAI",
                                                    "description": "Highest quality Speech AI model made by AssemblyAI",
                                                    "pricing": "Pay-per-second",
                                                    "reliability": "high",
                                                    "price": 0.045,
                                                    "languages_supported": [
                                                        {
                                                            "language_code": "auto",
                                                            "language_name": "automatic selection"
                                                        },
                                                        {
                                                            "language_code": "en",
                                                            "language_name": "english"
                                                        },
                                                        {
                                                            "language_code": "en_au",
                                                            "language_name": "english (Australia)"
                                                        },
                                                        {
                                                            "language_code": "en_uk",
                                                            "language_name": "english"
                                                        },
                                                        {
                                                            "language_code": "en_us",
                                                            "language_name": "english (United States)"
                                                        },
                                                        {
                                                            "language_code": "es",
                                                            "language_name": "spanish"
                                                        },
                                                        {
                                                            "language_code": "fr",
                                                            "language_name": "french"
                                                        },
                                                        {
                                                            "language_code": "de",
                                                            "language_name": "german"
                                                        },
                                                        {
                                                            "language_code": "it",
                                                            "language_name": "italian"
                                                        },
                                                        {
                                                            "language_code": "pt",
                                                            "language_name": "portuguese"
                                                        },
                                                        {
                                                            "language_code": "nl",
                                                            "language_name": "dutch"
                                                        },
                                                        {
                                                            "language_code": "hi",
                                                            "language_name": "hindi"
                                                        },
                                                        {
                                                            "language_code": "ja",
                                                            "language_name": "japanese"
                                                        },
                                                        {
                                                            "language_code": "zh",
                                                            "language_name": "chinese"
                                                        },
                                                        {
                                                            "language_code": "fi",
                                                            "language_name": "finnish"
                                                        },
                                                        {
                                                            "language_code": "ko",
                                                            "language_name": "korean"
                                                        },
                                                        {
                                                            "language_code": "pl",
                                                            "language_name": "polish"
                                                        },
                                                        {
                                                            "language_code": "ru",
                                                            "language_name": "russian"
                                                        },
                                                        {
                                                            "language_code": "tr",
                                                            "language_name": "turkish"
                                                        },
                                                        {
                                                            "language_code": "uk",
                                                            "language_name": "ukrainian"
                                                        },
                                                        {
                                                            "language_code": "vi",
                                                            "language_name": "vietnamese"
                                                        }
                                                    ]
                                                },
                                                {
                                                    "name": "nano",
                                                    "display_name": "Nano",
                                                    "description": "Low cost Speech AI model made by AssemblyAI",
                                                    "pricing": "Pay-per-second",
                                                    "reliability": "high",
                                                    "price": 0.015,
                                                    "languages_supported": [
                                                        {
                                                            "language_code": "auto",
                                                            "language_name": "automatic selection"
                                                        },
                                                        {
                                                            "language_code": "en",
                                                            "language_name": "english"
                                                        },
                                                        {
                                                            "language_code": "en_au",
                                                            "language_name": "english (Australia)"
                                                        },
                                                        {
                                                            "language_code": "en_uk",
                                                            "language_name": "english"
                                                        },
                                                        {
                                                            "language_code": "en_us",
                                                            "language_name": "english (United States)"
                                                        },
                                                        {
                                                            "language_code": "es",
                                                            "language_name": "spanish"
                                                        },
                                                        {
                                                            "language_code": "fr",
                                                            "language_name": "french"
                                                        },
                                                        {
                                                            "language_code": "de",
                                                            "language_name": "german"
                                                        },
                                                        {
                                                            "language_code": "it",
                                                            "language_name": "italian"
                                                        },
                                                        {
                                                            "language_code": "pt",
                                                            "language_name": "portuguese"
                                                        },
                                                        {
                                                            "language_code": "nl",
                                                            "language_name": "dutch"
                                                        },
                                                        {
                                                            "language_code": "af",
                                                            "language_name": "afrikaans"
                                                        },
                                                        {
                                                            "language_code": "sq",
                                                            "language_name": "albanian"
                                                        },
                                                        {
                                                            "language_code": "am",
                                                            "language_name": "amharic"
                                                        },
                                                        {
                                                            "language_code": "ar",
                                                            "language_name": "arabic"
                                                        },
                                                        {
                                                            "language_code": "hy",
                                                            "language_name": "armenian"
                                                        },
                                                        {
                                                            "language_code": "as",
                                                            "language_name": "assamese"
                                                        },
                                                        {
                                                            "language_code": "az",
                                                            "language_name": "azerbaijani"
                                                        },
                                                        {
                                                            "language_code": "ba",
                                                            "language_name": "bashkir"
                                                        },
                                                        {
                                                            "language_code": "eu",
                                                            "language_name": "basque"
                                                        },
                                                        {
                                                            "language_code": "be",
                                                            "language_name": "belarusian"
                                                        },
                                                        {
                                                            "language_code": "bn",
                                                            "language_name": "bengali"
                                                        },
                                                        {
                                                            "language_code": "bs",
                                                            "language_name": "bosnian"
                                                        },
                                                        {
                                                            "language_code": "br",
                                                            "language_name": "breton"
                                                        },
                                                        {
                                                            "language_code": "bg",
                                                            "language_name": "bulgarian"
                                                        },
                                                        {
                                                            "language_code": "my",
                                                            "language_name": "burmese"
                                                        },
                                                        {
                                                            "language_code": "ca",
                                                            "language_name": "catalan"
                                                        },
                                                        {
                                                            "language_code": "zh",
                                                            "language_name": "chinese"
                                                        },
                                                        {
                                                            "language_code": "hr",
                                                            "language_name": "croatian"
                                                        },
                                                        {
                                                            "language_code": "cs",
                                                            "language_name": "czech"
                                                        },
                                                        {
                                                            "language_code": "da",
                                                            "language_name": "danish"
                                                        },
                                                        {
                                                            "language_code": "et",
                                                            "language_name": "estonian"
                                                        },
                                                        {
                                                            "language_code": "fo",
                                                            "language_name": "faroese"
                                                        },
                                                        {
                                                            "language_code": "fi",
                                                            "language_name": "finnish"
                                                        },
                                                        {
                                                            "language_code": "gl",
                                                            "language_name": "galician"
                                                        },
                                                        {
                                                            "language_code": "ka",
                                                            "language_name": "georgian"
                                                        },
                                                        {
                                                            "language_code": "el",
                                                            "language_name": "greek"
                                                        },
                                                        {
                                                            "language_code": "gu",
                                                            "language_name": "gujarati"
                                                        },
                                                        {
                                                            "language_code": "ht",
                                                            "language_name": "haitian, haitian creole"
                                                        },
                                                        {
                                                            "language_code": "ha",
                                                            "language_name": "hausa"
                                                        },
                                                        {
                                                            "language_code": "haw",
                                                            "language_name": "hawaiian"
                                                        },
                                                        {
                                                            "language_code": "he",
                                                            "language_name": "hebrew"
                                                        },
                                                        {
                                                            "language_code": "hi",
                                                            "language_name": "hindi"
                                                        },
                                                        {
                                                            "language_code": "hu",
                                                            "language_name": "hungarian"
                                                        },
                                                        {
                                                            "language_code": "is",
                                                            "language_name": "icelandic"
                                                        },
                                                        {
                                                            "language_code": "id",
                                                            "language_name": "indonesian"
                                                        },
                                                        {
                                                            "language_code": "ja",
                                                            "language_name": "japanese"
                                                        },
                                                        {
                                                            "language_code": "jw",
                                                            "language_name": "jw"
                                                        },
                                                        {
                                                            "language_code": "kn",
                                                            "language_name": "kannada"
                                                        },
                                                        {
                                                            "language_code": "kk",
                                                            "language_name": "kazakh"
                                                        },
                                                        {
                                                            "language_code": "km",
                                                            "language_name": "khmer"
                                                        },
                                                        {
                                                            "language_code": "ko",
                                                            "language_name": "korean"
                                                        },
                                                        {
                                                            "language_code": "lo",
                                                            "language_name": "lao"
                                                        },
                                                        {
                                                            "language_code": "la",
                                                            "language_name": "latin"
                                                        },
                                                        {
                                                            "language_code": "lv",
                                                            "language_name": "latvian"
                                                        },
                                                        {
                                                            "language_code": "ln",
                                                            "language_name": "lingala"
                                                        },
                                                        {
                                                            "language_code": "lt",
                                                            "language_name": "lithuanian"
                                                        },
                                                        {
                                                            "language_code": "lb",
                                                            "language_name": "luxembourgish, letzeburgesch"
                                                        },
                                                        {
                                                            "language_code": "mk",
                                                            "language_name": "macedonian"
                                                        },
                                                        {
                                                            "language_code": "mg",
                                                            "language_name": "malagasy"
                                                        },
                                                        {
                                                            "language_code": "ms",
                                                            "language_name": "malay"
                                                        },
                                                        {
                                                            "language_code": "ml",
                                                            "language_name": "malayalam"
                                                        },
                                                        {
                                                            "language_code": "mt",
                                                            "language_name": "maltese"
                                                        },
                                                        {
                                                            "language_code": "mi",
                                                            "language_name": "māori"
                                                        },
                                                        {
                                                            "language_code": "mr",
                                                            "language_name": "marathi"
                                                        },
                                                        {
                                                            "language_code": "mn",
                                                            "language_name": "mongolian"
                                                        },
                                                        {
                                                            "language_code": "ne",
                                                            "language_name": "nepali"
                                                        },
                                                        {
                                                            "language_code": "no",
                                                            "language_name": "norwegian"
                                                        },
                                                        {
                                                            "language_code": "nn",
                                                            "language_name": "norwegian nynorsk"
                                                        },
                                                        {
                                                            "language_code": "oc",
                                                            "language_name": "occitan"
                                                        },
                                                        {
                                                            "language_code": "ps",
                                                            "language_name": "pashto"
                                                        },
                                                        {
                                                            "language_code": "fa",
                                                            "language_name": "persian"
                                                        },
                                                        {
                                                            "language_code": "pl",
                                                            "language_name": "polish"
                                                        },
                                                        {
                                                            "language_code": "ro",
                                                            "language_name": "romanian"
                                                        },
                                                        {
                                                            "language_code": "ru",
                                                            "language_name": "russian"
                                                        },
                                                        {
                                                            "language_code": "sa",
                                                            "language_name": "sanskrit (saṁskṛta)"
                                                        },
                                                        {
                                                            "language_code": "sr",
                                                            "language_name": "serbian"
                                                        },
                                                        {
                                                            "language_code": "sn",
                                                            "language_name": "shona"
                                                        },
                                                        {
                                                            "language_code": "sd",
                                                            "language_name": "sindhi"
                                                        },
                                                        {
                                                            "language_code": "si",
                                                            "language_name": "sinhala"
                                                        },
                                                        {
                                                            "language_code": "sk",
                                                            "language_name": "slovak"
                                                        },
                                                        {
                                                            "language_code": "sl",
                                                            "language_name": "slovenian"
                                                        },
                                                        {
                                                            "language_code": "so",
                                                            "language_name": "somali"
                                                        },
                                                        {
                                                            "language_code": "su",
                                                            "language_name": "sundanese"
                                                        },
                                                        {
                                                            "language_code": "sw",
                                                            "language_name": "swahili"
                                                        },
                                                        {
                                                            "language_code": "sv",
                                                            "language_name": "swedish"
                                                        },
                                                        {
                                                            "language_code": "tl",
                                                            "language_name": "tagalog"
                                                        },
                                                        {
                                                            "language_code": "tg",
                                                            "language_name": "tajik"
                                                        },
                                                        {
                                                            "language_code": "ta",
                                                            "language_name": "tamil"
                                                        },
                                                        {
                                                            "language_code": "tt",
                                                            "language_name": "tatar"
                                                        },
                                                        {
                                                            "language_code": "te",
                                                            "language_name": "telugu"
                                                        },
                                                        {
                                                            "language_code": "th",
                                                            "language_name": "thai"
                                                        },
                                                        {
                                                            "language_code": "bo",
                                                            "language_name": "tibetan"
                                                        },
                                                        {
                                                            "language_code": "tr",
                                                            "language_name": "turkish"
                                                        },
                                                        {
                                                            "language_code": "tk",
                                                            "language_name": "turkmen"
                                                        },
                                                        {
                                                            "language_code": "uk",
                                                            "language_name": "ukrainian"
                                                        },
                                                        {
                                                            "language_code": "ur",
                                                            "language_name": "urdu"
                                                        },
                                                        {
                                                            "language_code": "uz",
                                                            "language_name": "uzbek"
                                                        },
                                                        {
                                                            "language_code": "vi",
                                                            "language_name": "vietnamese"
                                                        },
                                                        {
                                                            "language_code": "cy",
                                                            "language_name": "welsh"
                                                        },
                                                        {
                                                            "language_code": "yi",
                                                            "language_name": "yiddish"
                                                        },
                                                        {
                                                            "language_code": "yo",
                                                            "language_name": "yoruba"
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    }
                                },
                                "examples": {
                                    "Example 1": {
                                        "value": {
                                            "data": [
                                                {
                                                    "name": "aws",
                                                    "display_name": "Amazon Transcribe",
                                                    "description": "Neural machine transcription by Amazon Web Service with suport for many languages for a premium price/",
                                                    "pricing": "Pay-per-second",
                                                    "reliability": "high",
                                                    "price": 0.132,
                                                    "languages_supported": [
                                                        {
                                                            "language_code": "auto",
                                                            "language_name": "automatic selection"
                                                        },
                                                        {
                                                            "language_code": "en",
                                                            "language_name": "english"
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "operationId": "transcription",
                "description": "Available transcription APIs and languages. User doesn't need to be authentificated.",
                "parameters": [
                    {
                        "schema": {
                            "type": "string"
                        },
                        "in": "header",
                        "name": "User-Agent",
                        "description": "<<{{APP_NAME}} v{{APP_VERSION}}>>"
                    }
                ],
                "x-internal": false,
                "security": [
                    {
                        "Api-Key": []
                    }
                ],
                "x-stoplight": {
                    "id": "ms3u3hhl9phcu"
                }
            }
        },
        "/ai/transcribe": {
            "post": {
                "summary": "AI Transcribe",
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {
                            "multipart/form-data": {
                                "schema": {
                                    "type": "object",
                                    "properties": {}
                                }
                            }
                        }
                    }
                },
                "operationId": "transcribe",
                "description": "**Transcribe** media (audio, video) file using AI into subtitles. Max size of file: 100 MB \n\nCredits on user account are needed. [Buy Credits](../open_api.json/paths/~1ai~1credits~1buy/get)\n\nCheck following method: [Get AI Transcribe status](../open_api.json/paths/~1ai~1transcribe~1{correlation_id}/get)\n\nMethod is returning \n```\n{\n  \"status\": \"CREATED\",\n  \"correlation_id\": \"67eda18f52e11\"\n}\n```\nStatus possible values: \n```\nCREATED     -> Initial state`\nPENDING     -> procedure is still running\nCOMPLETED   -> remote procedure call is completed and has a result\nERROR       -> procedure resulted in an error and is not running anymore\nTIMEOUT     -> No matching procedure call found before timeout\n```\nUsing `correlation_id` can check status of job using GET\n",
                "security": [
                    {
                        "Api-Key": []
                    },
                    {
                        "Bearer": []
                    }
                ],
                "parameters": [
                    {
                        "schema": {
                            "type": "string"
                        },
                        "in": "query",
                        "name": "api",
                        "description": "transcribe API",
                        "required": true
                    },
                    {
                        "schema": {
                            "type": "string"
                        },
                        "in": "query",
                        "description": "media file",
                        "required": true,
                        "name": "file"
                    },
                    {
                        "schema": {
                            "type": "string"
                        },
                        "in": "query",
                        "name": "language",
                        "description": "language of media file",
                        "required": true
                    }
                ],
                "tags": [
                    "AI Transcribe"
                ],
                "x-stoplight": {
                    "id": "2chhfrkbc30af"
                }
            },
            "parameters": []
        },
        "/ai/transcribe/{correlation_id}": {
            "get": {
                "summary": "AI Transcribe status",
                "responses": {
                    "200": {
                        "description": "OK"
                    }
                },
                "operationId": "transcribe-status",
                "security": [
                    {
                        "Api-Key": []
                    },
                    {
                        "Bearer": []
                    }
                ],
                "description": "Get status of **[transcribe](../open_api.json/paths/~1ai~1transcribe)** job using `correlation_id`",
                "x-stoplight": {
                    "id": "83cczlencci90"
                },
                "tags": [
                    "AI Transcribe"
                ]
            },
            "parameters": [
                {
                    "schema": {
                        "type": "string"
                    },
                    "name": "correlation_id",
                    "in": "path",
                    "required": true,
                    "description": "correlation_id"
                }
            ]
        },
        "/ai/detect_language_text": {
            "post": {
                "summary": "Detect Language Text",
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {
                            "multipart/form-data": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "data": {
                                            "type": "object",
                                            "properties": {
                                                "format": {
                                                    "type": "string"
                                                },
                                                "type": {
                                                    "type": "string"
                                                },
                                                "language": {
                                                    "type": "object",
                                                    "properties": {
                                                        "W3C": {
                                                            "type": "string"
                                                        },
                                                        "name": {
                                                            "type": "string"
                                                        },
                                                        "native": {
                                                            "type": "string"
                                                        },
                                                        "ISO_639_1": {
                                                            "type": "string"
                                                        },
                                                        "ISO_639_2b": {
                                                            "type": "string"
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    "x-examples": {
                                        "Example 1": {
                                            "data": {
                                                "format": "SubRip",
                                                "type": "text",
                                                "language": {
                                                    "W3C": "en",
                                                    "name": "english",
                                                    "native": "english",
                                                    "ISO_639_1": "en",
                                                    "ISO_639_2b": "eng"
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "operationId": "detect_language_text",
                "description": "**Detect language** of subtitle file.\n\nAt least 1 credits on user account is needed. [Buy Credits](../open_api.json/paths/~1ai~1credits~1buy/get)\n\nMethod is returning \n```\n{\n  \"data\": {\n    \"format\": \"SubRip\",\n    \"type\": \"text\",\n    \"language\": {\n      \"W3C\": \"en\",\n      \"name\": \"english\",\n      \"native\": \"english\",\n      \"ISO_639_1\": \"en\",\n      \"ISO_639_2b\": \"eng\"\n    }\n  }\n}\n```",
                "security": [
                    {
                        "Api-Key": []
                    },
                    {
                        "Bearer": []
                    }
                ],
                "parameters": [
                    {
                        "schema": {
                            "type": "string"
                        },
                        "in": "query",
                        "description": "subtitle file",
                        "required": true,
                        "name": "file"
                    }
                ],
                "x-stoplight": {
                    "id": "68wq42ph4db5n"
                },
                "x-internal": false,
                "tags": [
                    "Utilities"
                ]
            },
            "parameters": []
        },
        "/ai/detect_language_audio": {
            "post": {
                "summary": "Detect Language Audio",
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {
                            "multipart/form-data": {
                                "schema": {
                                    "type": "object",
                                    "properties": {}
                                }
                            }
                        }
                    }
                },
                "operationId": "detect_language_audio",
                "description": "**Detect language**  of media audio file. Max size of file: 100 MB \n\nAt least 1 credits on user account is needed. [Buy Credits](../open_api.json/paths/~1ai~1credits~1buy/get)\n\nCheck following method: [Get Detect Language Audio status](../open_api.json/paths/~1ai~1detect_language_audio~1{correlation_id}/get)\n\nMethod is returning \n```\n{\n  \"status\": \"CREATED\",\n  \"correlation_id\": \"67eda18f52e11\"\n}\n```\nStatus possible values: \n```\nCREATED     -> Initial state`\nPENDING     -> procedure is still running\nCOMPLETED   -> remote procedure call is completed and has a result\nERROR       -> procedure resulted in an error and is not running anymore\nTIMEOUT     -> No matching procedure call found before timeout\n```\nUsing `correlation_id` can check status of job using GET\n",
                "security": [
                    {
                        "Api-Key": []
                    },
                    {
                        "Bearer": []
                    }
                ],
                "parameters": [
                    {
                        "schema": {
                            "type": "string"
                        },
                        "in": "query",
                        "name": "api",
                        "description": "transcribe API",
                        "required": true
                    },
                    {
                        "schema": {
                            "type": "string"
                        },
                        "in": "query",
                        "description": "media file",
                        "required": true,
                        "name": "file"
                    },
                    {
                        "schema": {
                            "type": "string"
                        },
                        "in": "query",
                        "name": "language",
                        "description": "language of media file",
                        "required": true
                    }
                ],
                "x-stoplight": {
                    "id": "ps8b79w4p8i6k"
                },
                "tags": [
                    "Utilities"
                ]
            },
            "parameters": []
        },
        "/ai/detect_language_audio/{correlation_id}": {
            "get": {
                "summary": "Detect Language Audio Status",
                "responses": {
                    "200": {
                        "description": "OK"
                    }
                },
                "operationId": "detect-language-audio-status",
                "security": [
                    {
                        "Api-Key": []
                    },
                    {
                        "Bearer": []
                    }
                ],
                "description": "Get status of **[Detect Language Audio](../open_api.json/paths/~1ai~1detect_language_audio/post)** job using `correlation_id`\n",
                "x-stoplight": {
                    "id": "3fx0lqbfkrjkb"
                },
                "tags": [
                    "Utilities"
                ]
            },
            "parameters": [
                {
                    "schema": {
                        "type": "string"
                    },
                    "name": "correlation_id",
                    "in": "path",
                    "required": true,
                    "description": "correlation_id"
                }
            ]
        }
    },
    "components": {
        "schemas": {
            "Subtitle": {
                "type": "object",
                "x-tags": [
                    "Models"
                ],
                "properties": {
                    "id": {
                        "minLength": 1,
                        "type": "string"
                    },
                    "type": {
                        "minLength": 1,
                        "type": "string"
                    },
                    "attributes": {
                        "type": "object",
                        "required": [
                            "subtitle_id",
                            "language",
                            "download_count",
                            "new_download_count",
                            "from_trusted",
                            "foreign_parts_only",
                            "ai_translated",
                            "machine_translated",
                            "upload_date",
                            "feature_details",
                            "url",
                            "files"
                        ],
                        "properties": {
                            "subtitle_id": {
                                "minLength": 1,
                                "type": "string"
                            },
                            "language": {
                                "minLength": 1,
                                "type": "string"
                            },
                            "download_count": {
                                "type": "number"
                            },
                            "new_download_count": {
                                "type": "number"
                            },
                            "hearing_impaired": {
                                "type": "boolean"
                            },
                            "hd": {
                                "type": "boolean"
                            },
                            "fps": {
                                "type": "number"
                            },
                            "votes": {
                                "type": "number"
                            },
                            "points": {
                                "type": "number"
                            },
                            "ratings": {
                                "type": "number"
                            },
                            "from_trusted": {
                                "type": "boolean"
                            },
                            "foreign_parts_only": {
                                "type": "boolean"
                            },
                            "ai_translated": {
                                "type": "boolean"
                            },
                            "machine_translated": {
                                "type": "boolean"
                            },
                            "upload_date": {
                                "minLength": 1,
                                "type": "string"
                            },
                            "release": {
                                "minLength": 1,
                                "type": "string"
                            },
                            "comments": {
                                "type": "string"
                            },
                            "legacy_subtitle_id": {
                                "type": "number"
                            },
                            "uploader": {
                                "type": "object",
                                "properties": {
                                    "uploader_id": {
                                        "type": "number"
                                    },
                                    "name": {
                                        "type": "string"
                                    },
                                    "rank": {
                                        "type": "string"
                                    }
                                }
                            },
                            "feature_details": {
                                "type": "object",
                                "required": [
                                    "feature_id",
                                    "feature_type",
                                    "title",
                                    "movie_name",
                                    "imdb_id"
                                ],
                                "properties": {
                                    "feature_id": {
                                        "type": "number"
                                    },
                                    "feature_type": {
                                        "minLength": 1,
                                        "type": "string"
                                    },
                                    "year": {
                                        "type": "number"
                                    },
                                    "title": {
                                        "minLength": 1,
                                        "type": "string"
                                    },
                                    "movie_name": {
                                        "minLength": 1,
                                        "type": "string"
                                    },
                                    "imdb_id": {
                                        "type": "number"
                                    },
                                    "tmdb_id": {
                                        "type": "number"
                                    }
                                }
                            },
                            "url": {
                                "minLength": 1,
                                "type": "string"
                            },
                            "related_links": {
                                "type": "array",
                                "items": {
                                    "type": "object"
                                }
                            },
                            "files": {
                                "minItems": 1,
                                "uniqueItems": true,
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "file_id": {
                                            "type": "number"
                                        },
                                        "cd_number": {
                                            "type": "number"
                                        },
                                        "file_name": {
                                            "minLength": 1,
                                            "type": "string"
                                        },
                                        "": {
                                            "type": "string"
                                        }
                                    },
                                    "required": [
                                        "file_id",
                                        "file_name"
                                    ]
                                }
                            }
                        }
                    }
                },
                "required": [
                    "id",
                    "type",
                    "attributes"
                ]
            },
            "Feature-Tvshow": {
                "required": [
                    "attributes",
                    "id",
                    "type"
                ],
                "type": "object",
                "properties": {
                    "id": {
                        "minLength": 1,
                        "type": "string"
                    },
                    "type": {
                        "minLength": 1,
                        "type": "string"
                    },
                    "attributes": {
                        "required": [
                            "feature_id",
                            "imdb_id",
                            "img_url",
                            "original_title",
                            "seasons",
                            "subtitles_count",
                            "subtitles_counts",
                            "title",
                            "title_aka",
                            "tmdb_id",
                            "url",
                            "year"
                        ],
                        "type": "object",
                        "properties": {
                            "title": {
                                "minLength": 1,
                                "type": "string"
                            },
                            "original_title": {
                                "minLength": 1,
                                "type": "string"
                            },
                            "year": {
                                "minLength": 1,
                                "type": "string"
                            },
                            "imdb_id": {
                                "type": "number"
                            },
                            "tmdb_id": {
                                "type": "number"
                            },
                            "title_aka": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {}
                                }
                            },
                            "feature_id": {
                                "minLength": 1,
                                "type": "string"
                            },
                            "url": {
                                "minLength": 1,
                                "type": "string"
                            },
                            "img_url": {
                                "minLength": 1,
                                "type": "string"
                            },
                            "subtitles_counts": {
                                "required": [
                                    "ar",
                                    "bg",
                                    "bs",
                                    "ca",
                                    "cs",
                                    "da",
                                    "de",
                                    "el",
                                    "en",
                                    "es",
                                    "et",
                                    "fa",
                                    "fi",
                                    "fr",
                                    "he",
                                    "hr",
                                    "hu",
                                    "id",
                                    "it",
                                    "ja",
                                    "ko",
                                    "mk",
                                    "nl",
                                    "no",
                                    "pl",
                                    "pt-BR",
                                    "pt-PT",
                                    "ro",
                                    "ru",
                                    "sk",
                                    "sl",
                                    "sr",
                                    "sv",
                                    "th",
                                    "tr",
                                    "vi",
                                    "zh-CN",
                                    "zh-TW"
                                ],
                                "type": "object",
                                "properties": {
                                    "pl": {
                                        "type": "number"
                                    },
                                    "en": {
                                        "type": "number"
                                    },
                                    "pt-BR": {
                                        "type": "number"
                                    },
                                    "ro": {
                                        "type": "number"
                                    },
                                    "nl": {
                                        "type": "number"
                                    },
                                    "pt-PT": {
                                        "type": "number"
                                    },
                                    "es": {
                                        "type": "number"
                                    },
                                    "he": {
                                        "type": "number"
                                    },
                                    "hu": {
                                        "type": "number"
                                    },
                                    "el": {
                                        "type": "number"
                                    },
                                    "fr": {
                                        "type": "number"
                                    },
                                    "tr": {
                                        "type": "number"
                                    },
                                    "cs": {
                                        "type": "number"
                                    },
                                    "fi": {
                                        "type": "number"
                                    },
                                    "ar": {
                                        "type": "number"
                                    },
                                    "hr": {
                                        "type": "number"
                                    },
                                    "sl": {
                                        "type": "number"
                                    },
                                    "bg": {
                                        "type": "number"
                                    },
                                    "sr": {
                                        "type": "number"
                                    },
                                    "sv": {
                                        "type": "number"
                                    },
                                    "de": {
                                        "type": "number"
                                    },
                                    "et": {
                                        "type": "number"
                                    },
                                    "da": {
                                        "type": "number"
                                    },
                                    "bs": {
                                        "type": "number"
                                    },
                                    "it": {
                                        "type": "number"
                                    },
                                    "mk": {
                                        "type": "number"
                                    },
                                    "ru": {
                                        "type": "number"
                                    },
                                    "no": {
                                        "type": "number"
                                    },
                                    "th": {
                                        "type": "number"
                                    },
                                    "vi": {
                                        "type": "number"
                                    },
                                    "ja": {
                                        "type": "number"
                                    },
                                    "fa": {
                                        "type": "number"
                                    },
                                    "zh-CN": {
                                        "type": "number"
                                    },
                                    "ca": {
                                        "type": "number"
                                    },
                                    "id": {
                                        "type": "number"
                                    },
                                    "sk": {
                                        "type": "number"
                                    },
                                    "ko": {
                                        "type": "number"
                                    },
                                    "zh-TW": {
                                        "type": "number"
                                    }
                                }
                            },
                            "subtitles_count": {
                                "type": "number"
                            },
                            "seasons": {
                                "minItems": 1,
                                "uniqueItems": true,
                                "type": "array",
                                "items": {
                                    "required": [
                                        "season_number"
                                    ],
                                    "type": "object",
                                    "properties": {
                                        "season_number": {
                                            "type": "number"
                                        },
                                        "episodes": {
                                            "minItems": 1,
                                            "uniqueItems": true,
                                            "type": "array",
                                            "items": {
                                                "required": [
                                                    "episode_number",
                                                    "feature_id",
                                                    "feature_imdb_id",
                                                    "title"
                                                ],
                                                "type": "object",
                                                "properties": {
                                                    "episode_number": {
                                                        "type": "number"
                                                    },
                                                    "title": {
                                                        "minLength": 1,
                                                        "type": "string"
                                                    },
                                                    "feature_id": {
                                                        "type": "number"
                                                    },
                                                    "feature_imdb_id": {
                                                        "type": "number"
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "description": "",
                "x-tags": [
                    "Models"
                ]
            },
            "Feature-Episode": {
                "required": [
                    "attributes",
                    "id",
                    "type"
                ],
                "type": "object",
                "properties": {
                    "id": {
                        "minLength": 1,
                        "type": "string"
                    },
                    "type": {
                        "minLength": 1,
                        "type": "string"
                    },
                    "attributes": {
                        "required": [
                            "episode_number",
                            "feature_id",
                            "imdb_id",
                            "img_url",
                            "parent_title",
                            "season_number",
                            "subtitles_count",
                            "subtitles_counts",
                            "title",
                            "title_aka",
                            "tmdb_id",
                            "url",
                            "year"
                        ],
                        "type": "object",
                        "properties": {
                            "title": {
                                "minLength": 1,
                                "type": "string"
                            },
                            "original_title": {
                                "type": "object"
                            },
                            "year": {
                                "minLength": 1,
                                "type": "string"
                            },
                            "parent_imdb_id": {
                                "type": "object"
                            },
                            "parent_title": {
                                "minLength": 1,
                                "type": "string"
                            },
                            "season_number": {
                                "type": "number"
                            },
                            "episode_number": {
                                "type": "number"
                            },
                            "imdb_id": {
                                "type": "number"
                            },
                            "tmdb_id": {
                                "type": "number"
                            },
                            "title_aka": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {}
                                }
                            },
                            "feature_id": {
                                "minLength": 1,
                                "type": "string"
                            },
                            "url": {
                                "minLength": 1,
                                "type": "string"
                            },
                            "img_url": {
                                "minLength": 1,
                                "type": "string"
                            },
                            "subtitles_counts": {
                                "required": [
                                    "ar",
                                    "bg",
                                    "bs",
                                    "cs",
                                    "da",
                                    "de",
                                    "el",
                                    "en",
                                    "es",
                                    "et",
                                    "fi",
                                    "fr",
                                    "he",
                                    "hr",
                                    "hu",
                                    "mk",
                                    "nl",
                                    "no",
                                    "pl",
                                    "pt-BR",
                                    "pt-PT",
                                    "ro",
                                    "ru",
                                    "sl",
                                    "sr",
                                    "sv",
                                    "th",
                                    "tr"
                                ],
                                "type": "object",
                                "properties": {
                                    "pl": {
                                        "type": "number"
                                    },
                                    "en": {
                                        "type": "number"
                                    },
                                    "pt-BR": {
                                        "type": "number"
                                    },
                                    "es": {
                                        "type": "number"
                                    },
                                    "ro": {
                                        "type": "number"
                                    },
                                    "nl": {
                                        "type": "number"
                                    },
                                    "tr": {
                                        "type": "number"
                                    },
                                    "he": {
                                        "type": "number"
                                    },
                                    "pt-PT": {
                                        "type": "number"
                                    },
                                    "cs": {
                                        "type": "number"
                                    },
                                    "fi": {
                                        "type": "number"
                                    },
                                    "hu": {
                                        "type": "number"
                                    },
                                    "ar": {
                                        "type": "number"
                                    },
                                    "bg": {
                                        "type": "number"
                                    },
                                    "fr": {
                                        "type": "number"
                                    },
                                    "sl": {
                                        "type": "number"
                                    },
                                    "el": {
                                        "type": "number"
                                    },
                                    "hr": {
                                        "type": "number"
                                    },
                                    "sr": {
                                        "type": "number"
                                    },
                                    "et": {
                                        "type": "number"
                                    },
                                    "sv": {
                                        "type": "number"
                                    },
                                    "th": {
                                        "type": "number"
                                    },
                                    "bs": {
                                        "type": "number"
                                    },
                                    "da": {
                                        "type": "number"
                                    },
                                    "de": {
                                        "type": "number"
                                    },
                                    "mk": {
                                        "type": "number"
                                    },
                                    "no": {
                                        "type": "number"
                                    },
                                    "ru": {
                                        "type": "number"
                                    }
                                }
                            },
                            "subtitles_count": {
                                "type": "number"
                            }
                        }
                    }
                },
                "description": "",
                "x-tags": [
                    "Models"
                ]
            },
            "Feature-Movie": {
                "required": [
                    "attributes",
                    "id",
                    "type"
                ],
                "type": "object",
                "properties": {
                    "id": {
                        "minLength": 1,
                        "type": "string"
                    },
                    "type": {
                        "minLength": 1,
                        "type": "string"
                    },
                    "attributes": {
                        "required": [
                            "feature_id",
                            "feature_type",
                            "imdb_id",
                            "img_url",
                            "original_title",
                            "parent_title",
                            "season_number",
                            "seasons_count",
                            "subtitles_count",
                            "subtitles_counts",
                            "title",
                            "title_aka",
                            "tmdb_id",
                            "url",
                            "year"
                        ],
                        "type": "object",
                        "properties": {
                            "title": {
                                "minLength": 1,
                                "type": "string"
                            },
                            "original_title": {
                                "minLength": 1,
                                "type": "string"
                            },
                            "year": {
                                "minLength": 1,
                                "type": "string"
                            },
                            "subtitles_counts": {
                                "required": [
                                    "ar",
                                    "bg",
                                    "bn",
                                    "cs",
                                    "da",
                                    "de",
                                    "el",
                                    "en",
                                    "es",
                                    "et",
                                    "eu",
                                    "fa",
                                    "fi",
                                    "fr",
                                    "he",
                                    "hr",
                                    "hu",
                                    "id",
                                    "it",
                                    "ja",
                                    "ka",
                                    "ko",
                                    "lt",
                                    "mk",
                                    "ml",
                                    "ms",
                                    "nl",
                                    "no",
                                    "pl",
                                    "pt-BR",
                                    "pt-PT",
                                    "ro",
                                    "ru",
                                    "sk",
                                    "sl",
                                    "sr",
                                    "sv",
                                    "ta",
                                    "tr",
                                    "uk",
                                    "vi",
                                    "ze",
                                    "zh-CN",
                                    "zh-TW"
                                ],
                                "type": "object",
                                "properties": {
                                    "en": {
                                        "type": "number"
                                    },
                                    "pt-PT": {
                                        "type": "number"
                                    },
                                    "fi": {
                                        "type": "number"
                                    },
                                    "pt-BR": {
                                        "type": "number"
                                    },
                                    "es": {
                                        "type": "number"
                                    },
                                    "ar": {
                                        "type": "number"
                                    },
                                    "pl": {
                                        "type": "number"
                                    },
                                    "sr": {
                                        "type": "number"
                                    },
                                    "id": {
                                        "type": "number"
                                    },
                                    "ro": {
                                        "type": "number"
                                    },
                                    "zh-CN": {
                                        "type": "number"
                                    },
                                    "nl": {
                                        "type": "number"
                                    },
                                    "el": {
                                        "type": "number"
                                    },
                                    "hu": {
                                        "type": "number"
                                    },
                                    "fr": {
                                        "type": "number"
                                    },
                                    "sl": {
                                        "type": "number"
                                    },
                                    "tr": {
                                        "type": "number"
                                    },
                                    "et": {
                                        "type": "number"
                                    },
                                    "bg": {
                                        "type": "number"
                                    },
                                    "cs": {
                                        "type": "number"
                                    },
                                    "de": {
                                        "type": "number"
                                    },
                                    "he": {
                                        "type": "number"
                                    },
                                    "it": {
                                        "type": "number"
                                    },
                                    "vi": {
                                        "type": "number"
                                    },
                                    "hr": {
                                        "type": "number"
                                    },
                                    "ko": {
                                        "type": "number"
                                    },
                                    "no": {
                                        "type": "number"
                                    },
                                    "sv": {
                                        "type": "number"
                                    },
                                    "ta": {
                                        "type": "number"
                                    },
                                    "eu": {
                                        "type": "number"
                                    },
                                    "da": {
                                        "type": "number"
                                    },
                                    "fa": {
                                        "type": "number"
                                    },
                                    "sk": {
                                        "type": "number"
                                    },
                                    "uk": {
                                        "type": "number"
                                    },
                                    "zh-TW": {
                                        "type": "number"
                                    },
                                    "bn": {
                                        "type": "number"
                                    },
                                    "ka": {
                                        "type": "number"
                                    },
                                    "ja": {
                                        "type": "number"
                                    },
                                    "lt": {
                                        "type": "number"
                                    },
                                    "mk": {
                                        "type": "number"
                                    },
                                    "ml": {
                                        "type": "number"
                                    },
                                    "ms": {
                                        "type": "number"
                                    },
                                    "ru": {
                                        "type": "number"
                                    },
                                    "ze": {
                                        "type": "number"
                                    }
                                }
                            },
                            "subtitles_count": {
                                "type": "number"
                            },
                            "seasons_count": {
                                "type": "number"
                            },
                            "parent_title": {
                                "type": "string"
                            },
                            "season_number": {
                                "type": "number"
                            },
                            "episode_number": {
                                "type": "object"
                            },
                            "imdb_id": {
                                "type": "number"
                            },
                            "tmdb_id": {
                                "type": "number"
                            },
                            "parent_imdb_id": {
                                "type": "object"
                            },
                            "feature_id": {
                                "minLength": 1,
                                "type": "string"
                            },
                            "title_aka": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {}
                                }
                            },
                            "feature_type": {
                                "minLength": 1,
                                "type": "string"
                            },
                            "url": {
                                "minLength": 1,
                                "type": "string"
                            },
                            "img_url": {
                                "minLength": 1,
                                "type": "string"
                            }
                        }
                    }
                },
                "description": "",
                "x-tags": [
                    "Models"
                ]
            }
        },
        "securitySchemes": {
            "Api-Key": {
                "type": "apiKey",
                "description": "Application API key obtained in the user profile of app developer on opensubtitles.com to authorise the **application**",
                "name": "Api-Key",
                "in": "header"
            },
            "Bearer": {
                "type": "http",
                "description": "User token created in the login endpoint to authorise opensubtitles.com **user**",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            }
        }
    },
    "security": [
        {
            "Api-Key": []
        },
        {
            "Bearer": []
        }
    ]
}