from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import bcrypt

# --- Simulación de Base de Datos ---
# Registramos al usuario admin con su contraseña "adminpass" ya hasheada correctamente con bcrypt nativo
ADMIN_PASSWORD_PLAIN = "adminpass"
# Generamos el hash seguro de manera interna para la simulación
HASHED_PASSWORD_REAL = bcrypt.hashpw(ADMIN_PASSWORD_PLAIN.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

fake_db = {
    "admin": {
        "username": "admin",
        "hashed_password": HASHED_PASSWORD_REAL
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

    # Obtenemos el hash almacenado en formato de bytes para que bcrypt lo procese
    stored_hash_bytes = user_in_db["hashed_password"].encode('utf-8')
    # Obtenemos la contraseña digitada en texto plano en formato de bytes
    input_password_bytes = user_credentials.password.encode('utf-8')

    # Validamos usando la función nativa de bcrypt.checkpw
    # El hashing con salt aleatorio asegura las credenciales
    if not bcrypt.checkpw(input_password_bytes, stored_hash_bytes):
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
            response.raise_for_status()
            data = response.json()
            
            btc_price = data.get("bitcoin", {}).get("usd")
            
            if btc_price is None:
                raise HTTPException(status_code=500, detail="No se pudo obtener el precio de Bitcoin de la respuesta de la API.")

            return {"bitcoin_usd": btc_price}

        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Error al contactar la API de CoinGecko: {exc}")
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Ocurrió un error inesperado: {exc}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)