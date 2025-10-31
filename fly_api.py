from fastapi import FastAPI, HTTPException

app = FastAPI(
    
)

@app.get("/")
async def health_check():
    """
    Root endpoint with a welcome message.
    """
    return {"message": "we are healthy"}

@app.get("/linear_flight")
async def health_check():
    """
    Root endpoint with a welcome message.
    """
    return {"message": "we are flying"}