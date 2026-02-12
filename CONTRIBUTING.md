# Guia de Contribuição

Obrigado por considerar contribuir para o Dashboard Similaridade CAR-SIGEF! 🎉

## 🚀 Como Contribuir

### 1. Fork o Projeto

```bash
# Clone seu fork
git clone https://github.com/SEU_USUARIO/dashboard-similaridade-car-sigef.git
cd dashboard-similaridade-car-sigef
```

### 2. Configure o Ambiente

```bash
# Crie um ambiente virtual
python -m venv .venv

# Ative o ambiente virtual
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Instale as dependências
pip install -r requirements.txt
```

### 3. Configure as Variáveis de Ambiente

```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Configure suas credenciais no .env
# IMPORTANTE: NUNCA commite o arquivo .env!
```

### 4. Crie uma Branch

```bash
# Crie uma branch para sua feature/correção
git checkout -b feature/minha-feature
# ou
git checkout -b fix/meu-bugfix
```

### 5. Faça suas Alterações

#### Padrões de Código

- **Python**: Siga PEP 8
- **Docstrings**: Use Google Style
- **Type Hints**: Sempre que possível
- **Comentários**: Para lógica complexa

#### Exemplo de Docstring

```python
def minha_funcao(parametro: str, opcional: int = 10) -> bool:
    """Descrição curta da função.
    
    Descrição mais detalhada se necessário.
    
    Args:
        parametro: Descrição do parâmetro
        opcional: Descrição do parâmetro opcional
        
    Returns:
        Descrição do que retorna
        
    Raises:
        ValueError: Quando ocorre X
    """
    pass
```

### 6. Teste suas Alterações

```bash
# Execute a aplicação localmente
streamlit run app.py

# Verifique que:
# - [ ] Aplicação inicia sem erros
# - [ ] Filtros funcionam corretamente
# - [ ] Gráficos renderizam
# - [ ] Performance é aceitável
```

### 7. Commit suas Mudanças

```bash
# Adicione os arquivos modificados
git add .

# Commit com mensagem descritiva
git commit -m "feat: adiciona nova funcionalidade X"
# ou
git commit -m "fix: corrige bug Y"
# ou
git commit -m "docs: atualiza documentação Z"
```

#### Convenção de Commits

Usamos [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` Nova funcionalidade
- `fix:` Correção de bug
- `docs:` Documentação
- `style:` Formatação, ponto-e-vírgula, etc
- `refactor:` Refatoração de código
- `perf:` Melhoria de performance
- `test:` Adicionar/modificar testes
- `chore:` Tarefas de manutenção

### 8. Push para o GitHub

```bash
git push origin feature/minha-feature
```

### 9. Abra um Pull Request

1. Vá para seu fork no GitHub
2. Clique em "Pull Request"
3. Preencha o template de PR
4. Aguarde review

## 📋 Checklist para Pull Requests

- [ ] Código segue os padrões do projeto
- [ ] Docstrings adicionadas/atualizadas
- [ ] README atualizado se necessário
- [ ] Testado localmente
- [ ] Sem erros de lint (se aplicável)
- [ ] Commits seguem convenção
- [ ] Branch atualizada com main/master

## 🐛 Reportando Bugs

Ao reportar um bug, inclua:

- **Descrição clara** do problema
- **Passos para reproduzir**
- **Comportamento esperado** vs **comportamento atual**
- **Screenshots** (se aplicável)
- **Versões**:
  - Python
  - Streamlit
  - Sistema Operacional

## 💡 Sugerindo Melhorias

Ao sugerir uma melhoria:

- **Descreva** a funcionalidade/melhoria
- **Justifique** por que seria útil
- **Proponha** uma implementação (se possível)

## 🔒 Segurança

**NUNCA commite:**

- Arquivo `.env` com credenciais
- Senhas ou tokens
- Dados sensíveis

Se encontrar uma vulnerabilidade de segurança:

1. **NÃO** abra uma issue pública
2. Envie um email para: denner.caleare@estudante.ufla.br
3. Descreva a vulnerabilidade de forma clara

## 📝 Estrutura do Projeto

```
dashboard-similaridade-car-sigef/
├── app.py                  # Aplicação principal Streamlit
├── src/
│   ├── config/
│   │   └── __init__.py    # Configurações e constantes
│   └── utils/
│       └── __init__.py    # Funções DuckDB e visualização
├── data/                   # Dados (não versionados)
├── assets/                 # Recursos visuais
└── notebooks/              # Análises exploratórias
```

## 🎯 Áreas que Precisam de Contribuição

- [ ] Testes automatizados
- [ ] Otimização de performance
- [ ] Novas visualizações
- [ ] Melhorias na documentação
- [ ] Internacionalização (i18n)
- [ ] Acessibilidade (a11y)

## 📚 Recursos

- [Documentação Streamlit](https://docs.streamlit.io/)
- [DuckDB Documentation](https://duckdb.org/docs/)
- [Plotly Python](https://plotly.com/python/)
- [PEP 8 Style Guide](https://pep8.org/)

## 🙏 Agradecimentos

Seu tempo e esforço são muito apreciados! Obrigado por contribuir para tornar este projeto melhor! ❤️

---

**Dúvidas?** Abra uma issue ou entre em contato!
