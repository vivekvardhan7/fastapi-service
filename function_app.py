import azure.functions as func
import logging
from fast_api import analyze_video_endpoint

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="http_trigger")
def http_trigger(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    video_url = req.params.get('video_url')
    if not video_url:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            video_url = req_body.get('video_url')

    if video_url:
        result=analyze_video_endpoint(video_url)
        return func.HttpResponse(f"{result}",status_code=500)
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a video_url in the query string or in the request body for a personalized response.",
             status_code=200
        )