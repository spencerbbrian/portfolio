{% macro currency_format(column_name, currency_symbol='$') %}

    CONCAT('{{ currency_symbol }}', ROUND( {{column_name }}::NUMERIC, 2 ))

{% endmacro %}