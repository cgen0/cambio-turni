# README - Cambio Turni Bot
## Descrizione

Questo bot è stato progettato per gestire gli annunci relativi allo scambio dei turni di lavoro. Gli annunci inseriti dagli utenti verranno pubblicati su un canale di cui **il bot deve essere amministratore**.\
L'applicazione è eseguita tramite una Lambda Function di AWS e utilizza un API Gateway come trigger per ricevere gli aggiornamenti da Telegram ed un EventBridge come trigger temporale per la pulizia degli annunci scaduti.\
Inoltre, memorizza dati su due tabelle all'interno di Amazon DynamoDB: _announce_ per gli annunci del bot e _persistence_ per la persistenza delle conversazioni.\

## Prerequisiti

Prima di procedere con la configurazione del bot, è necessario soddisfare i seguenti prerequisiti:

1. **Bot Telegram**: Deve essere già stato creato e configurato un bot Telegram. Per le istruzioni su come creare un bot Telegram, consultare la [documentazione ufficiale](https://core.telegram.org/bots#how-do-i-create-a-bot).
2. **Canale e Gruppo di Controllo**: Deve essere giá stato creato il canale Telegram dove verranno pubblicati gli annunci ed il gruppo Telegram di controllo dei membri. Il bot deve essere amministratore sia del canale che del gruppo.
3. **Account AWS**: È richiesto un account Amazon Web Services (AWS) per l'esecuzione di questa applicazione. Se non si possiede ancora un account AWS, è possibile registrarne uno seguendo il processo di registrazione disponibile sul [sito web di AWS](https://aws.amazon.com/).


## Configurazione della Lambda Function

### Creazione 
Il primo passo consiste nella creazione di una nuova [Lambda Function](https://docs.aws.amazon.com/lambda/), selezionando come ambiente di runtime `Python 3.8` e come architettura `x86_64`.


### Upload del Codice

Il codice che deve essere eseguito dalla funzione può essere caricato utilizzando il file `deployment-package.zip` presente nella repository.
É inoltre necessario creare un layer custom che contenga il file `libs.zip` con le dipendenze richieste e collegarlo alla funzione per garantire che le librerie necessarie siano disponibili durante l'esecuzione. Entrambi gli archivi sono generati dallo script `create_packages.sh`.

### Variabili d'Ambiente

Il corretto funzionamento del bot richiede che siano definite le seguenti variabili d'ambiente:

| Variabile d'Ambiente       | Valore                                                  |
| -------------------------- | --------------------------------------------------------|
|```ACCESS_KEY_ID```         | AWS Access Key ID                                       |
|```REGION```                | Regione in cui risiedono i servizi AWS (es: _eu-west-3_)|
|```SECRET_ACCESS_KEY```     | AWS Secret Access Key                                   |
|```TOKEN```                 | Token del bot Telegram                                  |
|```CHANNEL_ID```            | ID del canale dove appariranno gli annunci              |
|```CONTROL_GROUP_ID```      | ID del gruppo di discussione del canale                 |


### Configurazione generale

La Lambda Function deve essere configurata in modo specifico per garantire il corretto funzionamento del bot:

- **Timeout**: Il timeout della Lambda Function deve essere impostato a 2 minuti.

Questa impostazione riduce al minimo la possibilitá che l'esecuzione della funzione venga interrotta durante delle operazioni eccezionalmente lunghe.

## Configurazione del Database
Il bot utilizza Amazon DynamoDB per la memorizzazione dei dati. È necessario creare due tabelle all'interno di DynamoDB: una chiamata _announce_ e l'altra chiamata _persistence_.

#### Tabella _announce_

- **Nome della Tabella**: `announce`
- **Chiave di Partizione (Partition Key)**: `message_id` (Tipo: Numero - N)

La tabella verrà utilizzata per memorizzare gli annunci del bot. Il campo `message_id` verrà utilizzato come chiave primaria per identificare univocamente ciascun annuncio.

#### Tabella _persistence_

- **Nome della Tabella**: `persistence`
- **Chiave di Partizione (Partition Key)**: `type` (Tipo: Stringa - S)

La tabella verrà utilizzata per memorizzare le informazioni di persistenza delle conversazioni degli utenti.



## Configurazione dell'API Gateway

Per consentire al bot di ricevere aggiornamenti da Telegram tramite un webhook, è necessario configurare un trigger API Gateway HTTP per la Lambda Function dalla sezione Triggers.

Una volta creato l'API Gateway ed ottenuto il suo endpoint é necessario aprire l'URL https://api.telegram.org/bot[TOKEN]/setWebhook?url=[ENDPOINT], dove [TOKEN] é il TOKEN del bot Telegram mentre [ENDPOINT] é l'endpoint dell'API Gateway. 

La risposta dovrebbe essere simile a questa:
```{"ok":true,"result":true,"description":"Webhook was set"}```

Si possono verificare le informazioni relative al webhook aprendo l'URL https://api.telegram.org/bot[TOKEN]/getWebhookInfo.

## Configurazione dell'EventBridge

Per fare in modo che gli annunci scaduti vengano automaticamente eliminati, è necessario configurare un trigger EventBridge (CloudWatch Events) per la Lambda Function dalla sezione Triggers.

Il Trigger dovrá avere come schedule expression: ```cron(0 2 * * ? *)```, questo avvierá l'azione di pulizia avverrá ogni giorno alle 02:00.

## Licenza

Questo progetto è rilasciato sotto GNU General Public License v3.0. Consulta il file [LICENSE](LICENSE) per ulteriori dettagli.
