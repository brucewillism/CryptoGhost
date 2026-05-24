# CryptoGhost — Guia Tributário Básico (Brasil)

> **Aviso legal**: Este documento é informativo e não constitui assessoria fiscal ou jurídica. Consulte um contador especializado.

## Obrigações para Pessoa Física

Operações com criptoativos no Brasil devem ser declaradas à **Receita Federal**.

### O que declarar

1. **Bens e Direitos** (ficha de criptoativos) — saldo em 31/12
2. **Ganhos de Capital** — lucros em vendas acima do limite de isenção mensal
3. **Operações mensais** — via GCAP quando aplicável

### Isenção mensal

Atualmente, vendas de criptoativos com lucro **até R$ 35.000/mês** podem ser isentas para pessoa física (verifique legislação vigente).

### Alíquota

Lucros tributáveis: alíquota de **15%** (ganho de capital).

### Registro CryptoGhost

O CryptoGhost registra automaticamente:

- Todas as ordens (`orders`)
- Movimentações financeiras (`audit_logs` tipo `financial`)
- P&L por operação (`positions`)

### Exportação para declaração

Consulte os logs de auditoria e ordens via dashboard ou API:

```
GET /api/v1/dashboard/audit-logs?event_type=financial
GET /api/v1/trading/orders
```

### Recomendações

1. Mantenha planilha mensal consolidada de operações
2. Registre custo de aquisição (preço médio)
3. Declare mesmo em paper trading se migrar para live
4. Consulte IN RFB sobre criptoativos atualizada

### Responsabilidade

Bruce e família são responsáveis pela declaração correta de todos os ganhos/perdas em contas **próprias**.
