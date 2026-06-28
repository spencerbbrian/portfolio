import functions_framework
from google.cloud import bigquery

@functions_framework.http
def main(request):
    """
    HTTP-triggered cloud function called by Cloud Scheduler.
    Runs a placeholder query to prove trigger to function and bigquery path works end to end.
    """

    client = bigquery.Client()

    query = "SELECT CURRENT_TIMESTAMP() AS triggered_at"
    result = list(client.query(query).resut())

    triggered_at = result[0]["triggered_at"]

    return {
        "status": "ok",
        "message": f"retain trigger fired at {triggered_at}",
    }, 200