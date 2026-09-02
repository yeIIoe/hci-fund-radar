//+------------------------------------------------------------------+
//| HCI_CalendarBridge.mq5  —  MQL5 Service                          |
//| Entrega o calendario economico do MetaTrader em NDJSON.          |
//+------------------------------------------------------------------+
//
//  POR QUE EXISTE
//    O leitor do MACRO DIRECTION precisa do valor DIVULGADO no instante em que sai. O feed
//    gratuito do Forex Factory da previsao e anterior, mas NAO traz o resultado — conferido
//    tres vezes em 01 e 02/set/2026. O MetaTrader tem o calendario completo embutido, mas o
//    pacote Python dele nao expoe funcao nenhuma de calendario (verificado na maquina do
//    Eduardo: MetaTrader5 5.0.5735, zero funcoes com "calendar"). Entao a leitura acontece
//    aqui e chega ao Python por arquivo.
//
//  COMO
//    CalendarValueLast() devolve so o que MUDOU desde a ultima chamada. E o mecanismo de
//    push: quando um numero e divulgado, ele aparece na proxima volta. Banco local, sem rede,
//    sem limite de requisicao.
//
//  🔴 O QUE FOI CONSERTADO NESTA VERSAO (02/set)
//    A versao anterior fazia `Val(v) = (v==LONG_MIN) ? 0.0 : v/1e6`, ou seja, campo VAZIO
//    virava 0.0. Com isso "sem previsao" e "previsao de 0,0%" ficavam IDENTICOS no arquivo,
//    e so havia flag para actual e para o revisado — nao para forecast nem previous.
//    Isso nao e teorico: o CPI mensal da Suica tem previsao de 0,0% no calendario desta
//    semana. O leitor teria classificado um valor legitimo como ausente, ou pior, o inverso.
//    Agora cada campo sai como numero OU como null, e ha flag para os quatro.
//    E o mesmo genero de bug que nos custou o dia 31: valor plausivel, silenciosamente errado.
//
//  INSTALACAO E USO — ver mt5/INSTALAR.md
//+------------------------------------------------------------------+
#property service
#property strict
#property copyright "HCI - Hoki's Capital Insights"
#property version   "2.00"
#property description "Calendario economico do MT5 -> NDJSON para o MACRO DIRECTION"

input int    PollMs   = 200;                      // polling do banco LOCAL (sem rede)
input string OutFile  = "hci_calendar.ndjson";    // vai para MQL5\Files\
input string StatFile = "hci_bridge_status.json"; // batimento, para o Python saber se vive

ulong g_change_id = 0;
long  g_voltas    = 0;
long  g_emitidos  = 0;

//--- numero OU null. Nunca 0.0 para representar ausencia.
string Num(long v)
  {
   if(v == LONG_MIN) return("null");
   return(StringFormat("%.6f", (double)v / 1000000.0));
  }
string Flag(long v){ return (v == LONG_MIN) ? "false" : "true"; }

string Esc(string s)
  {
   StringReplace(s, "\\", "\\\\");
   StringReplace(s, "\"", "\\\"");
   StringReplace(s, "\n", " ");
   StringReplace(s, "\r", " ");
   StringReplace(s, "\t", " ");
   return(s);
  }

void Emit(const MqlCalendarValue &v)
  {
   MqlCalendarEvent ev;
   if(!CalendarEventById(v.event_id, ev)) return;
   MqlCalendarCountry co;
   CalendarCountryById(ev.country_id, co);

   // latencia MEDIDA: intervalo entre o horario do EVENTO e o instante em que o valor
   // apareceu aqui. E o numero que ninguem tinha — decide se a ponte serve para disparar
   // na noticia ou so para arquivar. Relatos de forum vao de 15 s a mais de 2 minutos.
   string lat = "null";
   if(v.actual_value != LONG_MIN && v.time > 0)
      lat = IntegerToString((long)(TimeCurrent() - v.time) * 1000);

   string j = StringFormat(
     "{\"lido_em\":\"%s\",\"t_event\":\"%s\",\"periodo\":\"%s\",\"value_id\":%I64u,"
     "\"event_id\":%I64u,\"country\":\"%s\",\"currency\":\"%s\",\"name\":\"%s\","
     "\"importance\":%d,\"revision\":%d,"
     "\"actual\":%s,\"forecast\":%s,\"prev\":%s,\"revised_prev\":%s,"
     "\"has_actual\":%s,\"has_forecast\":%s,\"has_prev\":%s,\"has_revised\":%s,"
     "\"latencia_ms\":%s,\"change_id\":%I64u}",
     TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS),
     TimeToString(v.time, TIME_DATE|TIME_SECONDS),
     TimeToString(v.period, TIME_DATE),
     v.id, v.event_id, co.code, co.currency, Esc(ev.name),
     (int)ev.importance, v.revision,
     Num(v.actual_value), Num(v.forecast_value),
     Num(v.prev_value), Num(v.revised_prev_value),
     Flag(v.actual_value), Flag(v.forecast_value),
     Flag(v.prev_value), Flag(v.revised_prev_value),
     lat, g_change_id);

   int h = FileOpen(OutFile, FILE_READ|FILE_WRITE|FILE_TXT|FILE_ANSI|
                             FILE_SHARE_READ|FILE_SHARE_WRITE);
   if(h != INVALID_HANDLE)
     {
      FileSeek(h, 0, SEEK_END);
      FileWriteString(h, j + "\r\n");
      FileClose(h);
      g_emitidos++;
     }
  }

//--- batimento: sem isto o Python nao distingue "nada mudou" de "ponte morta"
void Batimento()
  {
   int h = FileOpen(StatFile, FILE_WRITE|FILE_TXT|FILE_ANSI);
   if(h == INVALID_HANDLE) return;
   FileWriteString(h, StringFormat(
     "{\"vivo_em\":\"%s\",\"voltas\":%I64d,\"emitidos\":%I64d,\"change_id\":%I64u,"
     "\"poll_ms\":%d,\"servidor\":\"%s\",\"conta\":%I64d,\"gmt_offset_h\":%d}",
     TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS), g_voltas, g_emitidos,
     g_change_id, PollMs, AccountInfoString(ACCOUNT_SERVER),
     AccountInfoInteger(ACCOUNT_LOGIN),
     (int)((TimeCurrent() - TimeGMT()) / 3600)));
   FileClose(h);
  }

void OnStart()
  {
   MqlCalendarValue vals[];
   // A primeira chamada com change_id=0 SINCRONIZA e devolve o id corrente. Sem ela, a
   // primeira volta despejaria o historico inteiro como se fosse novidade.
   CalendarValueLast(g_change_id, vals);
   PrintFormat("HCI bridge v2: sincronizado, change_id=%I64u, poll=%dms", g_change_id, PollMs);
   Batimento();

   datetime ultimoBat = TimeCurrent();
   while(!IsStopped())
     {
      g_voltas++;
      ulong prev = g_change_id;
      int n = CalendarValueLast(g_change_id, vals);
      if(n > 0 && g_change_id != prev)
        {
         for(int i = 0; i < n; i++) Emit(vals[i]);
         PrintFormat("HCI bridge: %d valor(es) novo(s), change_id=%I64u", n, g_change_id);
         Batimento();
         ultimoBat = TimeCurrent();
        }
      else if(TimeCurrent() - ultimoBat >= 30)   // batimento a cada 30 s mesmo parado
        {
         Batimento();
         ultimoBat = TimeCurrent();
        }
      Sleep(PollMs);
     }
   PrintFormat("HCI bridge encerrado. %I64d voltas, %I64d valores emitidos.",
               g_voltas, g_emitidos);
  }
//+------------------------------------------------------------------+
