-- ====================================================================
-- MathAI - Schema Relacional (SQLite)
-- Fundação de Dados com suporte a Multi-usuário, Repetição Espaçada (SM-2)
-- e Dataset de Treino para IA Própria (Visão Multimodal & Metacognição)
-- ====================================================================

PRAGMA foreign_keys = ON;

-- 1. Tabela de Usuários / Alunos (Cadastro, Login & Onboarding)
-- O 'id' autoincrementado gerado aqui é o identificador único (aluno_id)
-- referenciado como Foreign Key em todas as tabelas de atividade do estudante.
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    senha_hash TEXT NOT NULL,              -- SHA-256 da senha
    cpf TEXT,                              -- Formato: 000.000.000-00 (necessário para emissão de NF e pagamentos)
    idade INTEGER CHECK (idade BETWEEN 5 AND 120),
    celular TEXT,                          -- Celular / WhatsApp com DDD
    cep TEXT,                              -- CEP para faturamento (00000-000)
    logradouro TEXT,
    numero TEXT,
    bairro TEXT,
    cidade TEXT,
    estado TEXT,
    motivos TEXT,                          -- JSON array ex: '["concurso_militar","melhoria_propria"]'
    escolaridade TEXT,                     -- Ex: 'Ensino Médio', 'Graduação', 'Mestrado'
    faculdade TEXT,                        -- Ex: 'USP', 'UFF', 'ITA' ou nome digitado
    curso TEXT,                            -- Ex: 'Matemática', 'Engenharia Civil'
    concursos_foco TEXT,                   -- JSON array ex: '["ESA","EFOMM","AFA"]'
    verificado INTEGER NOT NULL DEFAULT 0, -- 0: pendente de código 2FA / 1: verificado
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tabela de Códigos de Verificação (2FA / OTP)
-- Registra códigos de 6 dígitos gerados para ativação de conta ou login.
CREATE TABLE IF NOT EXISTS codigos_verificacao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    codigo TEXT NOT NULL,
    expira_em TIMESTAMP NOT NULL,
    usado INTEGER NOT NULL DEFAULT 0,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Tabela de Sessões Lembradas (Token de Navegador)
CREATE TABLE IF NOT EXISTS sessoes_lembradas (
    token TEXT PRIMARY KEY,
    usuario_id INTEGER NOT NULL,
    expira_em TIMESTAMP NOT NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
);

-- 4. Tabela de Questões
-- Armazena o banco de problemas com enunciados em LaTeX, figuras e metadados.
CREATE TABLE IF NOT EXISTS questoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    materia TEXT NOT NULL,                     -- Ex: 'Geometria Plana', 'Cálculo I', 'Álgebra Linear'
    topico TEXT NOT NULL,                      -- Ex: 'Semelhança de Triângulos', 'Derivadas', 'Espaços Vetoriais'
    subtopico TEXT,                            -- Ex: 'Teorema de Menelaus', 'Regra da Cadeia'
    dificuldade INTEGER CHECK (dificuldade IS NULL OR (dificuldade BETWEEN 1 AND 5)), -- Opcional: 1 a 5
    banca TEXT,                                -- Ex: 'ESA', 'ITA', 'OBMEP' ou Null
    ano INTEGER,                               -- Ex: 2023 (pode ser NULL para conteúdo genérico)
    enunciado TEXT NOT NULL,                   -- Suporta sintaxe LaTeX ($...$ ou $$...$$)
    figura_path TEXT,                          -- Caminho local ou URL de diagrama geométrico/gráfico
    gabarito TEXT,                             -- Resposta esperada ou expressão matemática final
    estrategias_esperadas TEXT,                -- JSON com lista de estratégias (ex: '["Tales", "Semelhança"]')
    tipo TEXT NOT NULL DEFAULT 'objetiva'      -- 'objetiva' (A-E) ou 'discursiva' (aberta / prova)
        CHECK (tipo IN ('objetiva', 'discursiva')),
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Tabela de Conceitos & Gatilhos Cognitivos (Estilo Flashcards / Anki)
-- Mapeia os "gatilhos mentais": Quando vejo X -> Aplico Y.
CREATE TABLE IF NOT EXISTS conceitos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    materia TEXT NOT NULL,
    topico TEXT NOT NULL,
    nome TEXT NOT NULL,                        -- Ex: 'Teorema de Ceva', 'Substituição Trigonométrica'
    gatilho TEXT NOT NULL,                     -- Frente do card: 'Cevianas concorrentes em um triângulo qualquer'
    acao_ou_teorema TEXT NOT NULL,             -- Verso do card: 'Razão dos segmentos = 1 (Teorema de Ceva)'
    formula_latex TEXT,                        -- Ex: '$$\frac{AF}{FB} \cdot \frac{BD}{DC} \cdot \frac{CE}{EA} = 1$$'
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Tabela de Tentativas (Histórico de Resolução)
-- Registra cada sessão de estudo vinculada ao aluno_id: tempo, estratégia adotada, erro e metacognição.
CREATE TABLE IF NOT EXISTS tentativas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    questao_id INTEGER NOT NULL,
    aluno_id INTEGER NOT NULL,                 -- FK para usuarios (id gerado no cadastro)
    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tempo_segundos INTEGER NOT NULL CHECK (tempo_segundos >= 0),
    acertou INTEGER NOT NULL CHECK (acertou IN (0, 1)), -- Booleano no SQLite: 0 = Não, 1 = Sim
    estrategia_usada TEXT,                     -- Estratégia que o aluno efetivamente escolheu
    tipo_erro TEXT DEFAULT 'nenhum' CHECK (
        tipo_erro IN ('nenhum', 'conta_sinal', 'manipulacao_algebrica', 'conceitual', 'interpretacao', 'outro', 'simulado_incorreto')
    ),
    confianca_aluno INTEGER CHECK (confianca_aluno BETWEEN 1 AND 5), -- Metacognição (1=chutei, 5=certeza absoluta)
    anotacoes TEXT,
    imagem_resolucao_path TEXT,                -- Caminho do upload do print do tablet / caderno
    FOREIGN KEY (questao_id) REFERENCES questoes (id) ON DELETE CASCADE,
    FOREIGN KEY (aluno_id) REFERENCES usuarios (id) ON DELETE CASCADE
);

-- 7. Tabela de Repetição Espaçada (Spaced Repetition / Algoritmo SM-2)
-- Controla o ciclo de revisões individual por aluno.
CREATE TABLE IF NOT EXISTS revisao_espacada (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aluno_id INTEGER NOT NULL,                 -- FK para usuarios (id gerado no cadastro)
    item_tipo TEXT NOT NULL CHECK (item_tipo IN ('questao', 'conceito')),
    item_id INTEGER NOT NULL,                  -- ID referenciando a tabela 'questoes' ou 'conceitos'
    fator_facilidade REAL DEFAULT 2.5 CHECK (fator_facilidade >= 1.3), -- Ease Factor (EF) do algoritmo SM-2
    intervalo_dias INTEGER DEFAULT 1 CHECK (intervalo_dias >= 1),
    repeticoes INTEGER DEFAULT 0 CHECK (repeticoes >= 0),
    proxima_revisao DATE NOT NULL,             -- Data da próxima sessão recomendada (YYYY-MM-DD)
    ultima_revisao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (aluno_id, item_tipo, item_id),     -- 1 agendamento por item por aluno
    FOREIGN KEY (aluno_id) REFERENCES usuarios (id) ON DELETE CASCADE
);

-- 8. Tabela de Perfil do Aluno por Tópico (Métricas Agregadas / Cache de Performance)
-- Agrega a performance por estudante e por tópico para carregar instantaneamente o Dashboard.
CREATE TABLE IF NOT EXISTS perfil_aluno_topico (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aluno_id INTEGER NOT NULL,                 -- FK para usuarios (id gerado no cadastro)
    materia TEXT NOT NULL,
    topico TEXT NOT NULL,
    total_tentativas INTEGER DEFAULT 0 CHECK (total_tentativas >= 0),
    total_acertos INTEGER DEFAULT 0 CHECK (total_acertos >= 0),
    tempo_medio_segundos REAL DEFAULT 0.0 CHECK (tempo_medio_segundos >= 0.0),
    estrategia_favorita TEXT,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (aluno_id, materia, topico),
    FOREIGN KEY (aluno_id) REFERENCES usuarios (id) ON DELETE CASCADE
);

-- 9. Tabela de Diagnósticos de IA (Visão Multimodal & OCR)
-- Registra as transcrições em LaTeX e avaliações pedagógicas geradas pelo Gemini.
-- Serve como dataset de fine-tuning/treinamento para o modelo próprio em PyTorch.
CREATE TABLE IF NOT EXISTS diagnosticos_ia (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tentativa_id INTEGER,                      -- FK opcional para tentativas
    questao_id INTEGER NOT NULL,
    aluno_id INTEGER NOT NULL,                 -- FK para usuarios (id gerado no cadastro)
    modelo_gemini TEXT,                        -- Qual modelo Gemini foi usado
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    imagem_path TEXT,                          -- Caminho do print do tablet/caderno
    justificativa_texto TEXT,                  -- O que o aluno digitou
    transcricao_latex TEXT,                    -- Transcrição das expressões em LaTeX (par input→output para treino)
    passos_json TEXT,                          -- JSON array com os passos identificados
    estrategia_identificada TEXT,              -- Estratégia detectada pela IA
    status_resolucao TEXT,                     -- 'correto', 'erro_conta_sinal', etc.
    diagnostico TEXT,                          -- Parecer pedagógico detalhado
    linha_do_erro TEXT,                        -- Onde ocorreu a falha
    dica_proximo_passo TEXT,                   -- Provocação reflexiva
    FOREIGN KEY (questao_id) REFERENCES questoes (id) ON DELETE CASCADE,
    FOREIGN KEY (tentativa_id) REFERENCES tentativas (id) ON DELETE SET NULL,
    FOREIGN KEY (aluno_id) REFERENCES usuarios (id) ON DELETE CASCADE
);

-- 10. Tabela de Log de Dicas Socráticas (Dataset de Comportamento de Estudo)
-- Registra cada vez que um aluno pediu ajuda, em qual nível e o que o Gemini respondeu.
CREATE TABLE IF NOT EXISTS log_dicas_socraticas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    questao_id INTEGER NOT NULL,
    aluno_id INTEGER NOT NULL,                 -- FK para usuarios (id gerado no cadastro)
    nivel_dica INTEGER NOT NULL CHECK (nivel_dica BETWEEN 1 AND 5),
    texto_dica TEXT,                           -- Resposta do Gemini (para dataset de treino)
    modelo_gemini TEXT,                        -- Qual modelo gerou a dica
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (questao_id) REFERENCES questoes (id) ON DELETE CASCADE,
    FOREIGN KEY (aluno_id) REFERENCES usuarios (id) ON DELETE CASCADE
);

-- 11. Tabela de Reportes de Questões (Curadoria e Feedback de Qualidade)
CREATE TABLE IF NOT EXISTS questoes_reportadas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    questao_id INTEGER NOT NULL,
    aluno_id INTEGER,
    motivo TEXT NOT NULL,                     -- 'latex_quebrado', 'figura_problema', 'traducao_ruim', 'gabarito_errado', 'outro'
    descricao TEXT,                           -- Comentário livre
    status TEXT DEFAULT 'pendente',           -- 'pendente', 'em_analise', 'resolvido', 'descartado'
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (questao_id) REFERENCES questoes (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_questoes_reportadas_status ON questoes_reportadas (status);

-- ====================================================================
-- Índices para Performance de Consulta
-- ====================================================================
CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios (email);
CREATE INDEX IF NOT EXISTS idx_codigos_email_codigo ON codigos_verificacao (email, codigo);
CREATE INDEX IF NOT EXISTS idx_sessoes_token ON sessoes_lembradas (token);

CREATE INDEX IF NOT EXISTS idx_questoes_materia_topico ON questoes (materia, topico);

CREATE INDEX IF NOT EXISTS idx_tentativas_aluno ON tentativas (aluno_id);
CREATE INDEX IF NOT EXISTS idx_tentativas_questao_id ON tentativas (questao_id);
CREATE INDEX IF NOT EXISTS idx_tentativas_data ON tentativas (data_hora);

CREATE INDEX IF NOT EXISTS idx_revisao_aluno ON revisao_espacada (aluno_id, proxima_revisao);
CREATE INDEX IF NOT EXISTS idx_perfil_aluno ON perfil_aluno_topico (aluno_id);

CREATE INDEX IF NOT EXISTS idx_diagnosticos_aluno ON diagnosticos_ia (aluno_id);
CREATE INDEX IF NOT EXISTS idx_diagnosticos_questao ON diagnosticos_ia (questao_id);

CREATE INDEX IF NOT EXISTS idx_log_dicas_aluno ON log_dicas_socraticas (aluno_id, questao_id);
