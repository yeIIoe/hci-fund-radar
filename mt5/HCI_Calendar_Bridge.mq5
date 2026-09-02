//+------------------------------------------------------------------+
//|  HCI_Calendar_Bridge.mq5                                         |
//|  A ponte entre o calendario do MetaTrader e o MACRO DIRECTION.   |
//+------------------------------------------------------------------+
//
//  POR QUE ESTE ARQUIVO EXISTE
//    O leitor precisa do valor DIVULGADO no instante em que sai. O feed gratuito do Forex
//    Factory da previsao e anterior, mas NAO traz o resultado — verificado tres vezes.
//    O MetaTrader tem o calendario completo embutido, com actual, forecast e previous, para
//    as 8 moedas. Mas o pacote Python do MT5 NAO expoe nenhuma funcao de calendario
//    (verificado na maquina do Eduardo, versao 5.0.5735: zero funcoes com "calendar").
//    Entao a leitura tem que acontecer do lado MQL5 e ser entregue em arquivo.
//
//  COMO FUNCIONA
//    CalendarValueLast() devolve so o que MUDOU desde a ultima chamada, usando um change_id
//    que o proprio terminal mantem. Isso e o mecanismo de push: quando um numero e divulgado,
//    ele aparece aqui na proxima volta do laco. Nao ha rede, nao ha limite de requisicao —
//    e um banco local.
//
//  O QUE ELE ESCREVE (em MQL5/Files/)
//    hci_calendar_live.json   so o que mudou na ultima volta — e o gatilho
//    hci_calendar_full.json   a janela inteira, reescrita a cada FullSeconds
//    hci_bridge_status.json   batimento cardiaco, para o Python saber que a ponte esta viva
//
//  ⚠️ LATENCIA: nao comprovada. Relatos de forum MQL5 vao de 15 segundos a mais de 2 minutos,
//     e o proprio moderador da MetaQuotes escreveu que "atraso dentro de 1 minuto e normal".
//     A alegacao de "dezenas de milissegundos" e material de venda. O campo latencia_ms deste
//     arquivo mede o intervalo entre o horario do EVENTO e o momento em que o valor apareceu
//     aqui — assim a latencia real fica MEDIDA, nao assumida.
//
//  INSTALACAO — ver mt5/INSTALAR.md
//+------------------------------------------------------------------+
#property service
#property copyright "HCI - Hoki's Capital Insights"
#property version   "1.00"
#property description "Le o calendario economico do MT5 e entrega em JSON para o MACRO DIRECTION"

input int  PollSeconds  = 5;      // intervalo de leitura, em segundos
input int  FullSeconds  = 300;    // de quanto em quanto reescreve a janela inteira
input int  DiasAtras    = 3;      // quantos dias para tras a janela cheia cobre
input int  DiasFrente   = 14;     // quantos dias para frente
input bool SoOitoMoedas = true;   // limitar as 8 moedas do projeto

string MOEDAS[] = {"USD","EUR","GBP","JPY","AUD","NZD","CAD","CHF"};

//+------------------------------------------------------------------+
//| Valores do calendario vem multiplicados por 1.000.000 e usam      |
//| LONG_MIN para "vazio". Sem tratar isso, um campo ausente vira um  |
//| numero gigante e contamina tudo silenciosamente.                  |
//+------------------------------------------------------------------+
string ValorOuNulo(long v)
{
   if(v == LONG_MIN) return("null");
   return(StringFormat("%.6f", v / 1000000.0));
}

string EscapaJson(string s)
{
   StringReplace(s, "\\", "\\\\");
   StringReplace(s, "\"", "\\\"");
   StringReplace(s, "\n", " ");
   StringReplace(s, "\r", " ");
   StringReplace(s, "\t", " ");
   return(s);
}

string Importancia(ENUM_CALENDAR_EVENT_IMPORTANCE imp)
{
   switch(imp)
   {
      case CALENDAR_IMPORTANCE_LOW:      return("Low");
      case CALENDAR_IMPORTANCE_MODERATE: return("Medium");
      case CALENDAR_IMPORTANCE_HIGH:     return("High");
      default:                           return("None");
   }
}

bool MoedaInteressa(string moeda)
{
   if(!SoOitoMoedas) return(true);
   for(int i = 0; i < ArraySize(MOEDAS); i++)
      if(MOEDAS[i] == moeda) return(true);
   return(false);
}

//+------------------------------------------------------------------+
//| Monta a linha JSON de um valor do calendario.                     |
//| Devolve "" quando a moeda nao interessa ou o evento nao resolve.  |
//+------------------------------------------------------------------+
string LinhaJson(MqlCalendarValue &v, datetime agora)
{
   MqlCalendarEvent ev;
   if(!CalendarEventById(v.event_id, ev)) return("");

   MqlCalendarCountry pais;
   string moeda = "";
   if(CalendarCountryById(ev.country_id, pais)) moeda = pais.currency;
   if(!MoedaInteressa(moeda)) return("");

   // latencia MEDIDA: quanto tempo entre o evento e o valor chegar aqui.
   // So faz sentido quando ja ha resultado divulgado.
   string lat = "null";
   if(v.HasActualValue() && v.time > 0)
      lat = IntegerToString((long)(agora - v.time) * 1000);

   return(StringFormat(
      "{\"id\":%I64d,\"event_id\":%I64d,\"moeda\":\"%s\",\"pais\":\"%s\","
      "\"nome\":\"%s\",\"importancia\":\"%s\","
      "\"quando\":\"%s\",\"periodo\":\"%s\",\"revisao\":%d,"
      "\"actual\":%s,\"forecast\":%s,\"previous\":%s,\"previous_revisado\":%s,"
      "\"tem_actual\":%s,\"latencia_ms\":%s,\"lido_em\":\"%s\"}",
      v.id, v.event_id, moeda, EscapaJson(pais.name),
      EscapaJson(ev.name), Importancia(ev.importance),
      TimeToString(v.time, TIME_DATE|TIME_SECONDS),
      TimeToString(v.period, TIME_DATE),
      v.revision,
      ValorOuNulo(v.actual_value), ValorOuNulo(v.forecast_value),
      ValorOuNulo(v.prev_value), ValorOuNulo(v.revised_prev_value),
      (v.HasActualValue() ? "true" : "false"),
      lat,
      TimeToString(agora, TIME_DATE|TIME_SECONDS)));
}

bool Grava(string arquivo, string conteudo)
{
   // FILE_COMMON grava na pasta comum, visivel a qualquer terminal e ao Python.
   int h = FileOpen(arquivo, FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON);
   if(h == INVALID_HANDLE)
   {
      Print("HCI bridge: nao consegui abrir ", arquivo, " erro ", GetLastError());
      return(false);
   }
   FileWriteString(h, conteudo);
   FileClose(h);
   return(true);
}

//+------------------------------------------------------------------+
void OnStart()
{
   Print("HCI Calendar Bridge iniciado. Poll ", PollSeconds, "s, janela cheia a cada ",
         FullSeconds, "s.");

   ulong    change_id   = 0;
   datetime ultimoFull  = 0;
   long     voltas      = 0;
   long     totalMudan  = 0;

   while(!IsStopped())
   {
      datetime agora = TimeCurrent();
      voltas++;

      //--- 1) SO O QUE MUDOU. Este e o gatilho: quando um numero e divulgado, ele cai aqui.
      MqlCalendarValue mudou[];
      ulong novo_id = change_id;
      int n = CalendarValueLast(novo_id, mudou);

      if(n > 0)
      {
         string linhas = "";
         int contadas = 0;
         for(int i = 0; i < n; i++)
         {
            string l = LinhaJson(mudou[i], agora);
            if(l == "") continue;
            if(contadas > 0) linhas += ",\n  ";
            linhas += l;
            contadas++;
         }
         if(contadas > 0)
         {
            totalMudan += contadas;
            string js = StringFormat(
               "{\n \"gerado_em\":\"%s\",\n \"change_id\":%I64u,\n \"mudancas\":%d,\n"
               " \"eventos\":[\n  %s\n ]\n}",
               TimeToString(agora, TIME_DATE|TIME_SECONDS), novo_id, contadas, linhas);
            Grava("hci_calendar_live.json", js);
            Print("HCI bridge: ", contadas, " mudanca(s) gravada(s).");
         }
      }
      change_id = novo_id;

      //--- 2) A janela inteira, de tempos em tempos. Serve de base, nao de gatilho.
      if(agora - ultimoFull >= FullSeconds)
      {
         ultimoFull = agora;
         MqlCalendarValue todos[];
         datetime de  = agora - (datetime)DiasAtras  * 86400;
         datetime ate = agora + (datetime)DiasFrente * 86400;
         int m = CalendarValueHistory(todos, de, ate);
         string linhas = "";
         int contadas = 0;
         for(int i = 0; i < m; i++)
         {
            string l = LinhaJson(todos[i], agora);
            if(l == "") continue;
            if(contadas > 0) linhas += ",\n  ";
            linhas += l;
            contadas++;
         }
         string js = StringFormat(
            "{\n \"gerado_em\":\"%s\",\n \"de\":\"%s\",\n \"ate\":\"%s\",\n \"total\":%d,\n"
            " \"eventos\":[\n  %s\n ]\n}",
            TimeToString(agora, TIME_DATE|TIME_SECONDS),
            TimeToString(de, TIME_DATE), TimeToString(ate, TIME_DATE),
            contadas, linhas);
         Grava("hci_calendar_full.json", js);
      }

      //--- 3) Batimento. Sem isto o Python nao sabe distinguir "nada mudou" de "ponte morta".
      Grava("hci_bridge_status.json", StringFormat(
         "{\"vivo_em\":\"%s\",\"voltas\":%I64d,\"mudancas_total\":%I64d,"
         "\"change_id\":%I64u,\"poll_s\":%d,\"servidor\":\"%s\",\"conta\":%I64d}",
         TimeToString(agora, TIME_DATE|TIME_SECONDS), voltas, totalMudan, change_id,
         PollSeconds, AccountInfoString(ACCOUNT_SERVER), AccountInfoInteger(ACCOUNT_LOGIN)));

      Sleep(PollSeconds * 1000);
   }
   Print("HCI Calendar Bridge encerrado apos ", voltas, " voltas.");
}
//+------------------------------------------------------------------+
