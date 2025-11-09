## Prompt para Gemini: Construção da Aplicação "NVIDIA GPU Control & Monitor" do Zero

**Objetivo Principal:** Desenvolver uma aplicação gráfica (GUI) completa e funcional para Linux, em Python 3 com Tkinter, que permita aos utilizadores controlar e monitorizar as suas placas gráficas NVIDIA. A aplicação deve ser robusta, segura e incorporar todas as funcionalidades detalhadas abaixo, com especial atenção às complexidades de gestão de privilégios e ambiente gráfico.

---

### 1. Nome da Aplicação

**NVIDIA GPU Control & Monitor**

---

### 2. Requisitos Essenciais para o Ambiente de Execução

*   **Sistema Operativo:** Exclusivamente **Linux**.
*   **Hardware:** Placa gráfica NVIDIA com drivers proprietários instalados.
*   **Ferramentas de Sistema:** Dependência de `nvidia-settings` e `nvidia-smi` (devem estar instaladas e acessíveis no PATH).
*   **Linguagem/Framework:** Python 3 com a biblioteca `Tkinter`.

---

### 3. Funcionalidades a Implementar

#### 3.1. Controlo da GPU (Interface Gráfica)

*   **Velocidade da Ventoinha (Fan Speed):**
    *   Implementar um `ttk.Scale` (slider) para ajustar a velocidade da ventoinha em percentagem (intervalo: 30% a 100%).
    *   Exibir um `ttk.Label` adjacente ao slider mostrando o valor numérico atual em percentagem (ex: "75%").
    *   A aplicação deve ativar o controlo manual da ventoinha (`GPUFanControlState=1`) através de `nvidia-settings` sempre que uma alteração de ventoinha for aplicada.
*   **Offset do Core Clock:**
    *   Implementar um `ttk.Scale` para ajustar o offset do core clock em MHz (intervalo: 0 a +250 MHz).
    *   Exibir um `ttk.Label` adjacente ao slider mostrando o valor numérico atual em MHz (ex: "+150 MHz").
*   **Offset do Memory Clock:**
    *   Implementar um `ttk.Scale` para ajustar o offset do memory clock em MHz (intervalo: 0 a +1000 MHz).
    *   Exibir um `ttk.Label` adjacente ao slider mostrando o valor numérico atual em MHz (ex: "+750 MHz").
*   **Botão "Aplicar Alterações":**
    *   Um `ttk.Button` que, ao ser clicado, aplica todas as configurações atuais dos sliders à GPU. As alterações NÃO devem ser aplicadas instantaneamente ao mover os sliders.
*   **Botão "Repor Padrões":**
    *   Um `ttk.Button` que reverte todas as configurações: ventoinha para controlo automático (`GPUFanControlState=0`), offsets de core e memória para 0.

#### 3.2. Monitorização em Tempo Real (Interface Gráfica)

*   **Painel de Estatísticas:** Uma área de texto (`tk.Text` com `state=tk.DISABLED`) formatada para exibir informações atualizadas da GPU.
*   **Dados a Exibir:**
    *   Nome da GPU (obtido via `nvidia-smi`).
    *   Temperatura da GPU (°C, via `nvidia-smi`).
    *   Velocidade da Ventoinha (percentagem, lida de `GPUTargetFanSpeed` via `nvidia-settings` para refletir o valor *aplicado*, não o valor físico que pode ser impreciso).
    *   Uso da GPU (%, via `nvidia-smi`).
    *   Core Clock Atual (MHz, via `nvidia-smi`).
    *   Memory Clock Atual (MHz, via `nvidia-smi`).
    *   Consumo de Energia (W, via `nvidia-smi`) – deve lidar com valores `[N/A]` de forma elegante.
*   **Atualização:** As estatísticas devem ser atualizadas automaticamente a cada 2 segundos.
*   **Botão "Pausar/Retomar Monitor":** Um `ttk.Button` para alternar a atualização automática das estatísticas.

#### 3.3. Gestão de Perfis (Interface Gráfica)

*   **Guardar Perfil:**
    *   Um `ttk.Entry` para o utilizador inserir um nome para o perfil.
    *   Um `ttk.Button` "Guardar" que salva as configurações atuais dos sliders (fan, core, mem) como um novo perfil.
*   **Carregar Perfil:**
    *   Um `ttk.Combobox` (dropdown) listando todos os perfis guardados.
    *   Ao selecionar um perfil no dropdown, os sliders devem ser atualizados com as configurações do perfil e as alterações devem ser aplicadas automaticamente (como se o botão "Aplicar Alterações" tivesse sido clicado).
*   **Apagar Perfil:**
    *   Um `ttk.Button` "Apagar" para remover o perfil atualmente selecionado no `Combobox`. O perfil "Padrão" não pode ser apagado.
*   **Ficheiro de Perfis:** Os perfis devem ser armazenados num ficheiro `profiles.json` (formato JSON) no diretório da aplicação.
*   **Perfil Padrão:** A aplicação deve iniciar com um perfil "Padrão" pré-definido (ex: ventoinha 60%, core 150, mem 750) se nenhum perfil for carregado ou se o ficheiro `profiles.json` não existir.

#### 3.4. Logging e Diagnóstico

*   **Ficheiro de Log:** Todas as ações importantes (início da aplicação, tentativas de aplicação de configurações, erros, guardar/apagar perfis) devem ser registadas num ficheiro `nvidiaoc.log` no diretório da aplicação.
*   **Detalhes do Log:**
    *   Timestamp (`datetime.datetime.now()`) para cada entrada.
    *   Comandos `nvidia-settings` e `nvidia-smi` executados (o comando completo).
    *   Resultados (stdout/stderr) de comandos que falham, incluindo o código de saída.
    *   Verificação pós-aplicação: Após aplicar configurações, o log deve registar os valores lidos do hardware após um pequeno atraso (ex: 2 segundos) para confirmar o sucesso da operação.
*   **Limpeza do Log:** O ficheiro `nvidiaoc.log` deve ser limpo (recriado vazio) no início de cada execução da aplicação.

#### 3.5. Interface de Linha de Comando (CLI)

*   A aplicação deve suportar argumentos CLI para aplicar configurações ou repor padrões sem iniciar a GUI.
*   **Argumentos:** Utilizar `argparse`.
    *   `--fan VALOR`: Define a velocidade da ventoinha em percentagem.
    *   `--core VALOR`: Define o offset do core clock em MHz.
    *   `--mem VALOR`: Define o offset do memory clock em MHz.
    *   `--reset`: Flag (boolean) para repor todas as configurações para o padrão.
*   **Comportamento CLI:** Ao usar a CLI (se qualquer um dos argumentos `--fan`, `--core`, `--mem`, ou `--reset` for fornecido), a aplicação deve executar as ações correspondentes e sair, sem iniciar a GUI.

---

### 4. Robustez e Experiência do Utilizador (Instruções Cruciais para o Gemini)

#### 4.1. Gestão de Dependências (Tkinter)

*   **Verificação:** Ao iniciar, a aplicação deve verificar se o `Tkinter` está instalado (`try-except ImportError`).
*   **Instalação Automática:** Se não estiver, deve:
    *   Detetar a distribuição Linux (Arch, Debian/Ubuntu, Fedora e derivados) lendo `/etc/os-release`.
    *   Perguntar ao utilizador (via `input()` no terminal) se permite a instalação do pacote `python3-tk` (ou equivalente: `tk` para Arch, `python3-tkinter` para Fedora) usando o gestor de pacotes (`pacman`, `apt`, `dnf`) com `sudo`.
    *   Se permitido, executar o comando de instalação (`subprocess.Popen` ou `subprocess.run`).
    *   Após a instalação bem-sucedida, **reiniciar a própria aplicação automaticamente** (`os.execv(sys.executable, [sys.executable] + sys.argv)`) para que o `Tkinter` seja carregado.

#### 4.2. Gestão de Privilégios (`pkexec` e `xhost`) - **ATENÇÃO: Ponto Crítico!**

Esta é a parte mais complexa e onde a aplicação falhou anteriormente. O Gemini deve seguir estas instruções rigorosamente:

*   **Uso de `pkexec`:** Para todas as operações que modificam o hardware (comandos `nvidia-settings -a`), a aplicação DEVE usar `pkexec` para solicitar privilégios de administrador.
*   **Script Wrapper (`pkexec_wrapper.sh`):**
    *   Criar um script shell chamado `pkexec_wrapper.sh` no diretório da aplicação.
    *   Este script será executado por `pkexec`. A sua função é garantir que as variáveis de ambiente `DISPLAY` e `XAUTHORITY` são corretamente definidas para o comando `nvidia-settings` que será executado como `root`.
    *   **Conteúdo de `pkexec_wrapper.sh`:**
        ```bash
        #!/bin/bash
        # Wrapper script to preserve environment variables for pkexec
        # O primeiro argumento é o caminho para o ficheiro Xauthority
        XAUTH_PATH=$1
        shift # Remove o primeiro argumento

        # Verifica se o ficheiro Xauthority existe
        if [ -z "$XAUTH_PATH" ] || [ ! -f "$XAUTH_PATH" ]; then
            echo "Erro: Ficheiro Xauthority não encontrado ou não especificado em '$XAUTH_PATH'" >&2
            exit 1
        fi

        export DISPLAY=:0
        export XAUTHORITY=$XAUTH_PATH

        # Executa o comando real
        exec "$@"
        ```
    *   O script `pkexec_wrapper.sh` DEVE ser tornado executável (`chmod +x`).
*   **Gestão de `xhost` no `gpu_control.py`:**
    *   A função `run_command` em `gpu_control.py` (que executa os comandos `nvidia-settings` via `pkexec`) DEVE implementar a gestão de `xhost`.
    *   **Função `manage_xhost_permissions(action)`:** Criar uma função Python que executa `xhost +SI:localuser:root` (para adicionar permissão) ou `xhost -SI:localuser:root` (para remover permissão).
        *   Esta função DEVE ser executada como o utilizador normal (não como `root`).
        *   Deve garantir que `DISPLAY` e `XAUTHORITY` são passados corretamente para o comando `xhost` (usando o parâmetro `env` em `subprocess.run`).
    *   **Fluxo em `run_command`:**
        1.  Antes de chamar `pkexec` para um comando `nvidia-settings -a`, chamar `manage_xhost_permissions("add")`.
        2.  Executar o comando `pkexec` (via `subprocess.run`).
        3.  Usar um bloco `try...finally` para garantir que `manage_xhost_permissions("remove")` é SEMPRE chamado, mesmo que o comando `pkexec` falhe.
*   **Regra Polkit (`/etc/polkit-1/rules.d/90-nvidiaoc.rules`):**
    *   O Gemini DEVE informar o utilizador que ele precisa de criar este ficheiro no seu sistema com privilégios de `root`.
    *   **Conteúdo da Regra Polkit:**
        ```javascript
        // /etc/polkit-1/rules.d/90-nvidiaoc.rules
        polkit.addRule(function(action, subject) {
            if (action.id == "org.freedesktop.policykit.exec" &&
                action.lookup("program") == "/home/veezus/gemini/nvidiaoc/pkexec_wrapper.sh") { // Caminho completo para o wrapper
                
                // Permitir que as variáveis DISPLAY e XAUTHORITY sejam passadas do ambiente do utilizador que invoca
                action.set("environment", ["DISPLAY", "XAUTHORITY"]);
                
                // Manter o pedido de password (comportamento padrão)
                // polkit.Result.AUTH_ADMIN_REQUIRED é o padrão, não é necessário retornar explicitamente.
            }
        });
        ```
    *   O Gemini DEVE instruir o utilizador a reiniciar o serviço Polkit (`sudo systemctl restart polkit.service`) ou a sua sessão gráfica/computador após criar a regra.

#### 4.3. Tratamento de Erros

*   A aplicação deve lidar graciosamente com erros (ex: `nvidia-settings` não encontrado, falha na execução de comandos).
*   Mensagens de erro claras devem ser registadas no `nvidiaoc.log`, incluindo `stdout` e `stderr` completos dos comandos falhados.
*   A GUI deve permanecer responsiva mesmo que os comandos de backend falhem.

---

### 5. Design da Interface (Tkinter)

*   **Layout:** Organizado e intuitivo, com painéis para controlos, perfis e monitorização.
*   **Estilo:** Utilizar `ttk` para um visual mais moderno e nativo.
*   **Fontes:** Usar uma fonte monoespaçada para o painel de estatísticas para melhor legibilidade.
*   **Responsividade:** A janela deve ser redimensionável e os elementos devem ajustar-se razoavelmente.

---

### 6. Considerações de Segurança e Avisos

*   **RISCO DE OVERCLOCKING:** A aplicação deve exibir um aviso claro sobre os riscos de overclocking.
*   **Persistência:** As configurações aplicadas não são permanentes e serão perdidas ao reiniciar o computador (a menos que o utilizador configure um serviço de inicialização manual).

---

### 7. Ideias para Futuros Upgrades (Não para a versão inicial, mas para ter em mente)

*   **Persistência Automática:** Opção para criar um serviço `systemd` para aplicar configurações no arranque.
*   **Gráficos:** Visualização gráfica do histórico de temperatura, uso, etc.
*   **Suporte Multi-GPU:** Seleção da GPU a controlar em sistemas com múltiplas placas.
*   **Temas Visuais:** Opções de personalização da aparência da GUI.
*   **Notificações:** Alertas para temperaturas elevadas ou outros eventos.

---

### 8. Guia para o Processo de Desenvolvimento (Para o Gemini)

*   **Abordagem Iterativa:** Começa por implementar a estrutura básica da GUI e as funcionalidades de leitura de estatísticas (`nvidia-smi`).
*   **Prioridade:** A seguir, foca-te na implementação do controlo da GPU (`nvidia-settings`) com a gestão de privilégios (`pkexec`, `pkexec_wrapper.sh`, `xhost`) e a regra Polkit. Este é o ponto mais crítico e propenso a erros.
*   **Testes Rigorosos:** Testa cada componente de privilégios exaustivamente.
    *   **Problemas Potenciais:** O `pkexec` e o `xhost` são notoriamente difíceis de configurar corretamente devido às variações nos ambientes Linux e nas políticas de segurança.
    *   **Estratégia de Resolução:** Se surgirem erros relacionados com `pkexec` ou `xhost`, o Gemini deve:
        1.  **Verificar Logs:** Analisar os logs detalhados (`nvidiaoc.log`) para identificar a mensagem de erro exata.
        2.  **Interagir com o Utilizador:** Pedir ao utilizador para executar comandos de diagnóstico no seu terminal (ex: `echo $DISPLAY`, `echo $XAUTHORITY`, `ls -l /run/user/$(id -u)/xauth_*`) para obter informações sobre o seu ambiente.
        3.  **Ajustar a Regra Polkit/Wrapper:** Com base nos diagnósticos, ajustar a regra Polkit ou o script wrapper.
*   **Implementação de Perfis e CLI:** Após a funcionalidade principal estar estável, implementa a gestão de perfis e a interface CLI.
*   **Documentação:** Mantém o `README.md` atualizado com instruções claras para o utilizador, incluindo a necessidade da regra Polkit e como a instalar.
*   **Comunicação:** Informa o utilizador sobre cada passo importante, especialmente quando for necessária a sua intervenção (ex: criar a regra Polkit, reiniciar serviços).

Este prompt fornece um roteiro detalhado para a construção da aplicação, com ênfase nas áreas de maior complexidade e nos passos de depuração que se mostraram necessários.
