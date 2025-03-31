from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from typing import Optional
from app.utils.openai_client import get_openai_response
from app.utils.file_handler import save_upload_file_temporarily

# Import the functions you want to test directly
from app.utils.functions import *

app = FastAPI(title="IITM Assignment API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/")
async def process_question(
    question: str = Form(...), file: Optional[UploadFile] = File(None)
):
    try:
        # Save file temporarily if provided
        temp_file_path = None
        if file:
            temp_file_path = await save_upload_file_temporarily(file)

        # Get answer from OpenAI
        try:
            answer = await get_openai_response(question, temp_file_path)
            return {"answer": answer}
        except Exception as e:
            import traceback
            error_detail = {
                "error": str(e),
                "traceback": traceback.format_exc(),
                "question": question,
                "file_provided": file is not None
            }
            raise HTTPException(status_code=500, detail=error_detail)
    except Exception as e:
        import traceback
        raise HTTPException(
            status_code=500, 
            detail={
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        )


# New endpoint for testing specific functions
@app.post("/debug/{function_name}")
async def debug_function(
    function_name: str,
    file: Optional[UploadFile] = File(None),
    params: str = Form("{}"),
):
    """
    Debug endpoint to test specific functions directly

    Args:
        function_name: Name of the function to test
        file: Optional file upload
        params: JSON string of parameters to pass to the function
    """
    try:
        # Save file temporarily if provided
        temp_file_path = None
        if file:
            temp_file_path = await save_upload_file_temporarily(file)

        # Parse parameters
        parameters = json.loads(params)

        # Add file path to parameters if file was uploaded
        if temp_file_path:
            parameters["file_path"] = temp_file_path

        # Call the appropriate function based on function_name
        if function_name == "analyze_sales_with_phonetic_clustering":
            result = await analyze_sales_with_phonetic_clustering(**parameters)
            return {"result": result}
        elif function_name == "calculate_prettier_sha256":
            # For calculate_prettier_sha256, we need to pass the filename parameter
            if temp_file_path:
                result = await calculate_prettier_sha256(temp_file_path)
                return {"result": result}
            else:
                return {"error": "No file provided for calculate_prettier_sha256"}
        else:
            return {
                "error": f"Function {function_name} not supported for direct testing"
            }

    except Exception as e:
        import traceback

        return {"error": str(e), "traceback": traceback.format_exc()}


@app.post("/debug/transcribe")
async def debug_transcribe(
    youtube_url: str = Form(...),
    start_time: float = Form(...),
    end_time: float = Form(...)
):
    """
    Debug endpoint to test the transcribe_youtube_segment function
    """
    try:
        # Import the function directly to avoid any issues with circular imports
        from app.utils.functions import transcribe_youtube_segment
        
        # Call the function with the provided parameters
        result = await transcribe_youtube_segment(
            youtube_url=youtube_url,
            start_time=start_time,
            end_time=end_time
        )
        
        return {"result": result}
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@app.post("/debug/duckdb_query")
async def debug_duckdb_query(
    query_type: str = Form(...),
    timestamp_filter: Optional[str] = Form(None),
    numeric_filter: Optional[int] = Form(None),
    sort_order: Optional[str] = Form(None)
):
    """
    Debug endpoint to test the generate_duckdb_query function
    """
    try:
        # Import the function directly to avoid any issues with circular imports
        from app.utils.functions import generate_duckdb_query
        
        # Call the function with the provided parameters
        result = await generate_duckdb_query(
            query_type=query_type,
            timestamp_filter=timestamp_filter,
            numeric_filter=numeric_filter,
            sort_order=sort_order
        )
        
        return {"result": result}
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@app.post("/debug/openai_client")
async def debug_openai_client(question: str = Form(...)):
    """
    Debug endpoint to test the openai_client module
    """
    try:
        # Import necessary functions
        from app.utils.openai_client import get_openai_response
        import inspect
        import importlib
        
        # Collect information about modules and functions
        debug_info = {
            "question": question,
            "modules": {}
        }
        
        # Check if functions.py is importable
        try:
            from app.utils import functions
            functions_module = importlib.import_module("app.utils.functions")
            debug_info["modules"]["functions"] = {
                "importable": True,
                "functions": {
                    "transcribe_youtube_segment": hasattr(functions_module, "transcribe_youtube_segment"),
                    "generate_duckdb_query": hasattr(functions_module, "generate_duckdb_query")
                }
            }
            
            # Check if the functions actually exist and get their signatures
            if hasattr(functions_module, "transcribe_youtube_segment"):
                debug_info["modules"]["functions"]["transcribe_youtube_segment_signature"] = str(
                    inspect.signature(functions_module.transcribe_youtube_segment)
                )
            
            if hasattr(functions_module, "generate_duckdb_query"):
                debug_info["modules"]["functions"]["generate_duckdb_query_signature"] = str(
                    inspect.signature(functions_module.generate_duckdb_query)
                )
                
        except Exception as e:
            debug_info["modules"]["functions"] = {
                "importable": False,
                "error": str(e)
            }
            
        # Check if openai_client.py is importable
        try:
            from app.utils import openai_client
            openai_client_module = importlib.import_module("app.utils.openai_client")
            debug_info["modules"]["openai_client"] = {
                "importable": True,
                "functions": {
                    "get_openai_response": hasattr(openai_client_module, "get_openai_response")
                }
            }
            
            # Check if the function actually exists and get its signature
            if hasattr(openai_client_module, "get_openai_response"):
                debug_info["modules"]["openai_client"]["get_openai_response_signature"] = str(
                    inspect.signature(openai_client_module.get_openai_response)
                )
                
        except Exception as e:
            debug_info["modules"]["openai_client"] = {
                "importable": False,
                "error": str(e)
            }
        
        # Try to call get_openai_response with a simple question
        try:
            result = await get_openai_response(question)
            debug_info["openai_response"] = {
                "success": True,
                "result": result
            }
        except Exception as e:
            import traceback
            debug_info["openai_response"] = {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
            
        return debug_info
        
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
