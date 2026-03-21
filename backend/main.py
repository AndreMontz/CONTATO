import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/")
async def get_game_page():
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

class GameRoom:
    def __init__(self):
        self.players = {}
        self.reset_game_state()

    def reset_game_state(self):
        self.status = "LOBBY"
        self.word = ""
        self.difficulty = ""
        self.revealed_count = 1
        self.eaten_count = 0
        self.current_dica = None
        self.burnt_words = []
        self.used_dicas = []
        self.used_contacts = []
        self.contact_player = None
        self.contact_word = None
        self.timer_task = None

    def get_players_info(self):
        info = {}
        for role, data in self.players.items():
            info[role] = {"name": data["name"], "emoji": data["emoji"]}
        return info

    async def disconnect(self, websocket: WebSocket):
        role_to_remove = None
        for role, data in self.players.items():
            if data["ws"] == websocket:
                role_to_remove = role
                break
        
        if role_to_remove:
            del self.players[role_to_remove]
            self.reset_game_state()
            await self.broadcast({
                "event": "DISCONNECT", 
                "message": f"Um jogador desconectou. Partida reiniciada.",
                "players": self.get_players_info()
            })

    async def broadcast(self, message: dict):
        for data in self.players.values():
            await data["ws"].send_text(json.dumps(message))

    def check_difficulty(self, word: str, difficulty: str) -> bool:
        length = len(word)
        if difficulty == "FACIL" and 8 <= length <= 10: return True
        if difficulty == "MEDIO" and 5 <= length <= 7: return True
        if difficulty == "DIFICIL" and 3 <= length <= 4: return True
        return False

    async def penalize(self, reason: str):
        self.eaten_count += 1
        await self.broadcast({"event": "PENALIDADE", "reason": reason, "eaten": self.eaten_count})
        self.status = "AGUARDANDO_DICA"
        self.current_dica = None
        await self.check_game_over()

    async def check_game_over(self):
        letras_disponiveis = len(self.word) - self.eaten_count
        morte_subita = self.revealed_count >= letras_disponiveis
        if morte_subita:
            await self.broadcast({"event": "MORTE_SUBITA", "message": "Última chance! Acertem a palavra ou percam."})

    async def sync_timeout(self):
        await asyncio.sleep(10)
        if self.status == "SINCRONIA":
            await self.penalize("Tempo esgotado para sincronia!")

room = GameRoom()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text(json.dumps({"event": "LOBBY_UPDATE", "players": room.get_players_info()}))

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            action = payload.get("action")

            if action == "join" and room.status == "LOBBY":
                req_role = payload.get("role")
                name = payload.get("name")
                emoji = payload.get("emoji")

                assigned_role = None
                if req_role == "CEREBRO" and "A" not in room.players: assigned_role = "A"
                elif req_role == "ADIVINHADOR":
                    if "B" not in room.players: assigned_role = "B"
                    elif "C" not in room.players: assigned_role = "C"

                if assigned_role:
                    room.players[assigned_role] = {"ws": websocket, "name": name, "emoji": emoji}
                    await websocket.send_text(json.dumps({"event": "JOINED", "role": assigned_role}))
                    await room.broadcast({"event": "LOBBY_UPDATE", "players": room.get_players_info()})

                    if len(room.players) == 3:
                        room.status = "AGUARDANDO_PALAVRA"
                        await room.broadcast({"event": "GAME_START", "message": "A sala está cheia. O jogo vai começar!"})
                else:
                    await websocket.send_text(json.dumps({"event": "ERROR", "message": "Papel ocupado ou sala cheia."}))

            role = None
            for r, p_data in room.players.items():
                if p_data["ws"] == websocket:
                    role = r
                    break
            
            if not role: continue

            if action == "set_word" and role == "A" and room.status == "AGUARDANDO_PALAVRA":
                word = payload.get("word").upper()
                diff = payload.get("difficulty")
                if room.check_difficulty(word, diff):
                    room.word = word
                    room.difficulty = diff
                    room.status = "AGUARDANDO_DICA"
                    await room.broadcast({"event": "WORD_SET", "first_letter": word[0], "difficulty": diff})
                else:
                    await websocket.send_text(json.dumps({"event": "ERROR", "message": "Tamanho da palavra inválido."}))

            elif action == "send_dica" and role in ["B", "C"] and room.status == "AGUARDANDO_DICA":
                dica = payload.get("dica").upper()
                if dica in room.used_dicas:
                    await websocket.send_text(json.dumps({"event": "ERROR", "message": "Dica já usada!"}))
                    continue
                room.used_dicas.append(dica)
                room.current_dica = dica
                room.status = "CORRIDA"
                await room.broadcast({"event": "NOVA_DICA", "dica": dica, "sender": role, "sender_name": room.players[role]["name"]})

            elif action == "intervene" and role == "A" and room.status == "CORRIDA":
                attempt = payload.get("word").upper()
                if attempt != room.word and attempt.startswith(room.word[:room.revealed_count][-1]):
                    if attempt not in room.burnt_words:
                        room.burnt_words.append(attempt)
                        room.eaten_count += 1
                        await room.broadcast({
                            "event": "INTERVENCAO", "word": attempt, 
                            "eaten": room.eaten_count, "name": room.players["A"]["name"],
                            "burnt_list": room.burnt_words
                        })
                        await room.check_game_over()

            elif action == "contact" and role in ["B", "C"] and room.status == "CORRIDA":
                word = payload.get("word").upper()
                if word == room.current_dica or word in room.burnt_words or word in room.used_contacts:
                    await websocket.send_text(json.dumps({"event": "ERROR", "message": "Palavra inválida/repetida!"}))
                    continue

                room.contact_player = role
                room.contact_word = word
                room.status = "SINCRONIA"
                
                waiting_role = "C" if role == "B" else "B"
                waiting_name = room.players[waiting_role]["name"] if waiting_role in room.players else "Adversário"
                
                await room.broadcast({"event": "CONTATO_ACIONADO", "player": role, "name": room.players[role]["name"], "waiting_name": waiting_name})
                room.timer_task = asyncio.create_task(room.sync_timeout())

            elif action == "sync_word" and role in ["B", "C"] and role != room.contact_player and room.status == "SINCRONIA":
                if room.timer_task: room.timer_task.cancel()
                sync_word = payload.get("word").upper()
                
                room.status = "ANIMACAO" # Bloqueia inputs durante o show
                
                room.used_contacts.append(room.contact_word)
                if sync_word not in room.used_contacts: room.used_contacts.append(sync_word)

                name_1 = room.players[room.contact_player]["name"]
                name_2 = room.players[role]["name"]
                is_match = (room.contact_word == sync_word)

                # Dispara a contagem regressiva visual no frontend
                await room.broadcast({
                    "event": "INICIAR_CONTAGEM", 
                    "word_1": room.contact_word, "word_2": sync_word, 
                    "name_1": name_1, "name_2": name_2, "is_match": is_match
                })

                # O servidor espera a animação de "3, 2, 1, CONTATO!" terminar (6 segundos de show)
                await asyncio.sleep(6)

                # Aplica o resultado e notifica
                if is_match:
                    if room.contact_word == room.word:
                        await room.broadcast({"event": "VITORIA_BC", "message": f"{name_1} e {name_2} acertaram a palavra secreta!"})
                        room.status = "GAME_OVER"
                    else:
                        room.revealed_count += 1
                        room.status = "AGUARDANDO_DICA"
                        await room.broadcast({"event": "SUCESSO_SINC", "letras": room.word[:room.revealed_count]})
                        await room.check_game_over()
                else:
                    if sync_word == room.word or room.contact_word == room.word:
                        await room.broadcast({"event": "VITORIA_A", "message": f"{name_1} e {name_2} queimaram a palavra secreta!"})
                        room.status = "GAME_OVER"
                    else:
                        await room.penalize("As palavras não sincronizaram.")

    except WebSocketDisconnect:
        await room.disconnect(websocket)
