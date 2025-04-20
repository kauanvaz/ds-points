WITH tb_transactions AS (

    SELECT *
    FROM transactions
    WHERE dtTransaction < '{date}'
        AND dtTransaction >= DATE('{date}', '-21 days')

),

tb_freq AS (

    SELECT
        idCustomer,

        COUNT(DISTINCT DATE(dtTransaction)) as qtdDiasD21,
        COUNT(DISTINCT CASE WHEN dtTransaction > DATE('{date}', '-14 days') THEN DATE(dtTransaction) END) as qtdDiasD14,
        COUNT(DISTINCT CASE WHEN dtTransaction > DATE('{date}', '-7 days') THEN DATE(dtTransaction) END) as qtdDiasD7

    FROM tb_transactions
    GROUP BY idCustomer

),

tb_live_minutes AS (

    SELECT
        idCustomer,
        DATE(DATETIME(dtTransaction, '-3 hours')) AS dtTransactionDate,
        MIN(DATETIME(dtTransaction, '-3 hours')) AS dataInicio,
        MAX(DATETIME(dtTransaction, '-3 hours')) AS dataFim,
        (julianday(MAX(DATETIME(dtTransaction, '-3 hours'))) - julianday(MIN(DATETIME(dtTransaction, '-3 hours')))) * 24 * 60 AS liveMinutes
    FROM tb_transactions
    GROUP BY idCustomer, dtTransactionDate

),

tb_hours AS (

    SELECT
        idCustomer,
        AVG(liveMinutes) AS avgLiveMinutes,
        SUM(liveMinutes) AS sumLiveMinutes,
        MIN(liveMinutes) AS minLiveMinutes,
        MAX(liveMinutes) AS maxLiveMinutes
    FROM tb_live_minutes
    GROUP BY idCustomer

),

tb_vida AS (

    SELECT
        idCustomer,
        COUNT(DISTINCT idTransaction) AS qtdeTransacaoVida,
        COUNT(DISTINCT idTransaction) / MAX(julianday('{date}') - julianday(dtTransaction)) AS avgTransacaoDia
    FROM transactions
    WHERE dtTransaction < '{date}'
    GROUP BY idCustomer

),

tb_join AS (

    SELECT
        t1.*,
        t2.avgLiveMinutes,
        t2.sumLiveMinutes,
        t2.minLiveMinutes,
        t2.maxLiveMinutes,
        t3.qtdeTransacaoVida,
        t3.avgTransacaoDia
    FROM tb_freq AS t1
    LEFT JOIN tb_hours AS t2
        ON t1.idCustomer = t2.idCustomer
    LEFT JOIN tb_vida AS t3
        ON t1.idCustomer = t3.idCustomer
)

SELECT 
    '{date}' AS dtRef,
    *
FROM tb_join