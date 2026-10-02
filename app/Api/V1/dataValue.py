from fastapi import APIRouter

router = APIRouter()

data_table = []

@router.get("/data")
async def get_data(data : str):
    data_table.append(data)
    return {"data": data_table}
