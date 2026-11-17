// Simula aportes mensais com juros compostos e compara com guardar sem juros.

funcao real saldoComJuros(real taxa, inteiro meses, real aporte) {
  real saldo = 0.0;
  inteiro mes = 1;
  enquanto (mes <= meses) {
    saldo = saldo * (1.0 + taxa) + aporte;
    mes = mes + 1;
  }
  retorne saldo;
}

funcao vazio principal() {
  inteiro meses = 12;
  real aporte = 100.0;
  real total = saldoComJuros(0.01, meses, aporte);
  real totalSemJuros = aporte * meses;

  escreva("Simulacao de reserva: 12 aportes mensais de R$ 100");
  escreva("Saldo com rendimento de 1% ao mes:");
  escreva(total);
  escreva("Saldo sem rendimento:");
  escreva(totalSemJuros);
  escreva("Rendimento acumulado:");
  escreva(total - totalSemJuros);
}
