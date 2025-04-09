
SHUFFLE_WALLETS     = True                  # True | False - перемешивать ли кошельки
RETRY               = 3                     # кол-во попыток при ошибках / фейлах

RPCS                = {
    'ethereum'  : 'https://0xrpc.io/eth',
    'arbitrum'  : 'https://arbitrum.meowrpc.com',
    'optimism'  : 'https://1rpc.io/op',
    'base'      : 'https://0xrpc.io/base',
}


# --- ONCHAIN SETTINGS ---
SLEEP_AFTER_ACC     = [20, 40]              # задержка после каждого аккаунта 20-40 секунд

REGISTER_PARAMS     = {
    "tokens"                : [             # какие токены регистрировать для получения дропа
        "HYPER",
        # "stHYPER",
    ],
    "chains"                : [             # какие сети регистрировать для получения дропа
        # 'ethereum',
        'arbitrum',
        'optimism',
        'base',
    ]
}


# --- PERSONAL SETTINGS ---
PROXY_TYPE          = "mobile"              # "mobile" - для мобильных/резидентских прокси, указанных ниже | "file" - для статичных прокси из файла `proxies.txt`
PROXY               = 'http://log:pass@ip:port' # что бы не использовать прокси - оставьте как есть
CHANGE_IP_LINK      = 'https://changeip.mobileproxy.space/?proxy_key=...&format=json'

CAPTCHA_KEY         = ""                    # ключ от капчи @solvium_crypto_bot

TG_BOT_TOKEN        = ''                    # токен от тг бота (`12345:Abcde`) для уведомлений. если не нужно - оставляй пустым
TG_USER_ID          = []                    # тг айди куда должны приходить уведомления.