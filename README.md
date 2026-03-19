# CONTATO
O jogo "CONTATO" só que online e mal feito

Uma adaptação digital e em tempo real do clássico jogo de palavras "Contato", feito para ser jogado entre 3 pessoas em navegadores web. O jogo utiliza WebSockets para garantir comunicação instantânea, sistema de penalidades e animações imersivas.

## ✨ Funcionalidades
* **Multiplayer em Tempo Real:** Sincronização perfeita entre os jogadores usando WebSockets.
* **Sistema de Papéis:** Jogue como o **Cérebro** (quem define a palavra) ou como a dupla de **Adivinhadores**.
* **Barra de Vida Dinâmica:** Os erros da dupla "comem" as letras da palavra secreta, criando um sistema de morte súbita.
* **Condição de Corrida (Race Condition):** Mecânica de "quem digita mais rápido" entre a intervenção do Cérebro e o Contato dos Adivinhadores.
* **UI/UX Imersiva:** Animações de contagem regressiva, flashes de acerto/erro e timers globais na tela.

## 🛠️ Tecnologias Utilizadas
* **Backend:** Python 3, FastAPI, Uvicorn, WebSockets.
* **Frontend:** HTML5, CSS3, JavaScript (Vanilla).

---

## 🚀 Como Rodar Localmente

Para rodar o servidor na sua máquina e testar o jogo, siga os passos abaixo:

### 1. Pré-requisitos
Certifique-se de ter o [Python](https://www.python.org/downloads/) instalado no seu computador. Durante a instalação no Windows, lembre-se de marcar a opção **"Add python.exe to PATH"**.

### 2. Instale as dependências
Abra o terminal na pasta do projeto e instale o FastAPI e o Uvicorn rodando o comando:

```bash
python -m pip install fastapi uvicorn websockets
```

### 3. Inicie o Servidor
Com as bibliotecas instaladas, inicie o servidor local na porta 8080:

```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8080
```
*(Se o terminal avisar "Application startup complete", o servidor está rodando perfeitamente).*

### 4. Abra o Jogo
O jogo requer **exatamente 3 jogadores** para iniciar.
Para testar sozinho, abra o arquivo `index.html` em 3 abas diferentes do seu navegador. O jogo começará assim que a terceira aba entrar no Lobby.

---

## 🎮 Como Jogar (Tutorial Completo)

### O Objetivo
O jogo é um duelo mental de 1 contra 2.
* **O Cérebro (Jogador A):** Escolhe uma Palavra Secreta e tenta impedir que os outros jogadores a descubram, "queimando" as dicas deles.
* **Os Adivinhadores (Jogadores B e C):** Trabalham em equipe para adivinhar a Palavra Secreta através de dicas e "Contatos" sincronizados.

### O Fluxo da Partida
1. **O Início:** O Cérebro define a Dificuldade e digita uma Palavra Secreta. O jogo revela apenas a **primeira letra** dessa palavra para os Adivinhadores.
2. **A Dica:** Um dos Adivinhadores pensa em qualquer palavra que comece com a letra revelada e dá uma **Dica** de uma única palavra. *(Ex: Letra é F. Pensa em "Faca" e envia a dica "Corte").*
3. **A Corrida (Intervenção vs. Contato):** A dica está na mesa. Agora é uma corrida de digitação:
    * **O Cérebro** tenta adivinhar o que o jogador pensou. Se ele digitar "Faca" rápido o suficiente, a palavra é **Queimada** e a dupla perde uma letra (Letra Comida).
    * **O outro Adivinhador** tenta entender a dica. Se ele também pensar em "Faca" (ou "Foice"), ele digita a palavra e aciona o **CONTATO**, bloqueando o Cérebro.
4. **A Sincronia:** Se o Contato for acionado, o Adivinhador que deu a dica tem 10 segundos para digitar a palavra que ele havia pensado.
5. **A Revelação:** O jogo faz uma contagem ("3... 2... 1... CONTATO!") e revela as duas palavras digitadas pelos Adivinhadores.

### Acertos, Erros e a "Barra de Vida"
As letras da Palavra Secreta funcionam como a "vida" da dupla. 

* ✅ **Sincronia Perfeita (Mesma Palavra):** A dupla ganha a próxima letra da Palavra Secreta.
* ❌ **Erro de Sincronia (Palavras Diferentes):** A dupla é penalizada e uma letra é "Comida" da barra de vida.
* 🔥 **Intervenção do Cérebro:** Se o Cérebro queimar a palavra antes do contato, a dupla também perde uma letra.

### Como Ganhar ou Perder?
* **Vitória dos Adivinhadores:** Eles ganham se, durante uma Sincronia, falarem exatamente a Palavra Secreta.
* **Vitória do Cérebro:** O Cérebro vence se os Adivinhadores falarem a Palavra Secreta fora de sintonia (um acerta e o outro erra), ou se a barra de vida chegar à "Morte Súbita" e a dupla não conseguir adivinhar a palavra na última chance.
