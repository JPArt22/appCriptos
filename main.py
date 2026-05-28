from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from passlib.context import CryptContext
import httpx

# --- Configuración de Hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# --- Configuración de Hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Simulación de Base de Datos ---
# En una aplicación real, esto vendría de una base de datos.
# La contraseña 'adminpass' ha sido hasheada previamente.
# Puedes generar un nuevo hash con: pwd_context.hash("nueva_contraseña")
fake_db = {
    "admin": {
        "username": "admin",
        "hashed_password": "$2b$12$EixZaYVK1f72w20a/2Vn.e.1v.w/3j.Q.pY3.w/5k.Z.Y.K.X.O.a" 
    }
}

# --- Modelos Pydantic ---
class UserLogin(BaseModel):
    username: str
    password: str

# --- Aplicación FastAPI ---
app = FastAPI()

# --- Endpoints ---
@app.post("/api/v1/auth/login")
async def login(user_credentials: UserLogin):
    """
    Autentica a un usuario.
    """
    user_in_db = fake_db.get(user_credentials.username)
    if not user_in_db:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # El hashing con salt aleatorio asegura las credenciales
    if not pwd_context.verify(user_credentials.password, user_in_db["hashed_password"]):
        raise HTTPException(status_code=400, detail="Contraseña incorrecta")

    return {"message": f"Bienvenido {user_credentials.username}, autenticación exitosa"}


@app.get("/api/v1/crypto/ingest")
async def ingest_crypto_data():
    """
    Obtiene el precio actual de Bitcoin en USD desde CoinGecko.
    """
    coingecko_url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(coingecko_url)
            response.raise_for_status()  # Lanza una excepción para respuestas 4xx/5xx
            data = response.json()
            
            # Extraer el precio de la respuesta
            btc_price = data.get("bitcoin", {}).get("usd")
            
            if btc_price is None:
                raise HTTPException(status_code=500, detail="No se pudo obtener el precio de Bitcoin del a respuesta de la API.")

            return {"bitcoin_usd": btc_price}

        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Error al contactar la API de CoinGecko: {exc}")
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Ocurrió un error inesperado: {exc}")


# --- Ejecución (para desarrollo) ---
if __name__ == "__main__":
    import uvicorn
    # Para generar un nuevo hash para la DB:
    # print(pwd_context.hash("adminpass"))
    uvicorn.run(app, host="0.0.0.0", port=8000)
