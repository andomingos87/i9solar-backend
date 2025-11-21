import os
import json
import base64
import time
from typing import Optional
from fastapi import FastAPI, HTTPException, Header, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
import bcrypt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Supabase Client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("Warning: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set")

def get_supabase() -> Client:
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise HTTPException(status_code=500, detail="Server configuration error")
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

class ChangePasswordRequest(BaseModel):
    currentPassword: str
    newPassword: str

def verify_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token de autenticação não fornecido")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Add padding if necessary for base64 decoding
        token += '=' * (-len(token) % 4)
        decoded_bytes = base64.b64decode(token)
        token_data = json.loads(decoded_bytes.decode('utf-8'))
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")
        
    token_age = (time.time() * 1000) - (token_data.get("timestamp", 0))
    twenty_four_hours = 24 * 60 * 60 * 1000
    
    if token_age > twenty_four_hours:
        raise HTTPException(status_code=401, detail="Token expirado. Faça login novamente.")
        
    return token_data

@app.post("/admin-change-password")
async def admin_change_password(
    payload: ChangePasswordRequest,
    token_data: dict = Depends(verify_token)
):
    current_password = payload.currentPassword
    new_password = payload.newPassword
    
    if not current_password or not new_password:
        raise HTTPException(status_code=400, detail="Senha atual e nova senha são obrigatórias")
        
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="A nova senha deve ter pelo menos 8 caracteres")
        
    supabase = get_supabase()
    
    user_id = token_data.get("userId") or token_data.get("id")
    
    # Fetch admin user
    try:
        response = supabase.table("admin_users").select("*").eq("id", user_id).single().execute()
        admin_user = response.data
    except Exception as e:
        print(f"Error fetching user: {e}")
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
    if not admin_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
    stored_hash = admin_user.get("password_hash", "")
    
    # Verify current password
    is_valid = False
    try:
        # Check bcrypt
        if bcrypt.checkpw(current_password.encode('utf-8'), stored_hash.encode('utf-8')):
            is_valid = True
    except Exception as e:
        print(f"Bcrypt check failed: {e}")
        pass
        
    # Check legacy password (fallback)
    if not is_valid:
        legacy_hash = '$2a$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi'
        if current_password == 'admin123' and stored_hash == legacy_hash:
            is_valid = True
            
    if not is_valid:
        raise HTTPException(status_code=401, detail="Senha atual incorreta")
        
    # Hash new password
    try:
        salt = bcrypt.gensalt(rounds=10)
        new_hash = bcrypt.hashpw(new_password.encode('utf-8'), salt).decode('utf-8')
    except Exception as e:
        print(f"Error hashing password: {e}")
        raise HTTPException(status_code=500, detail="Erro ao processar nova senha")
        
    # Update password
    try:
        supabase.table("admin_users").update({"password_hash": new_hash}).eq("id", user_id).execute()
    except Exception as e:
        print(f"Error updating password: {e}")
        raise HTTPException(status_code=500, detail="Erro ao atualizar senha no banco de dados")
        
    return {"success": True, "message": "Senha alterada com sucesso"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

