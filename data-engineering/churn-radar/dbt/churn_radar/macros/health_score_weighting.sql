{% macro calculate_health_score(logins_last_30d, days_since_last_login, distinct_features_used, open_tickets, payment_failures, downgrades, upgrades) %}
{#
    Rules-based composite health score, 0-100. Starts from a neutral 50 and
    adds/subtracts points per signal, each capped so no single factor can
    dominate the score. Deliberately simple and fully explainable (every
    point can be traced back to a specific behavior) rather than a black-box
    model -- the standard first pass for a health score before a company
    invests in a trained ML model on top of it.

    Kept as a macro (rather than inlined into the mart SQL) so the whole
    scoring formula lives in one place and is easy to tune without touching
    the model that calls it.
#}
    greatest(0, least(100,
        50
        + least({{ logins_last_30d }} * 2, 20)                                   -- up to +20 for recent login activity
        - greatest(0, least(({{ days_since_last_login }} - 14) * 1, 20))         -- up to -20 the longer it's been since they logged in past a 14-day grace period
        + least({{ distinct_features_used }} * 2, 10)                            -- up to +10 for broad feature adoption
        - least({{ open_tickets }} * 5, 15)                                      -- up to -15 for unresolved support tickets
        - (case when {{ payment_failures }} > 0 then 15 else 0 end)              -- -15 flat if they've ever had a failed payment
        - least({{ downgrades }} * 10, 10)                                       -- up to -10 for downgrading their plan
        + least({{ upgrades }} * 5, 10)                                          -- up to +10 for upgrading their plan
    ))
{% endmacro %}
