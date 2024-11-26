import azure.functions as func
import logging
from main import analyze_video_endpoint 

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


@app.route(route="http_trigger", auth_level=func.AuthLevel.FUNCTION)
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
        result = analyze_video_endpoint(video_url)
        return func.HttpResponse(f"Result: {result}",status_code=500)
    else:
        return func.HttpResponse(
            "This HTTP-triggered function executed successfully. Please pass a video URL in the query string or request body for analysis.",
            status_code=200
        )
    
# video_url="https://drive.google.com/file/d/110CFWj_YTjPAyiduW_Gc2m_qH9YAvEqH/view"
