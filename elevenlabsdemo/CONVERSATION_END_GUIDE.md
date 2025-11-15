# Guide : Gérer la fin de conversation avec ElevenLabs

## Problème rencontré

Lorsque l'agent ElevenLabs atteint le noeud "Fin" dans le workflow, deux problèmes surviennent :

1. **L'agent ne répond plus mais la session ne se termine pas** - Le noeud "Fin" dans le workflow ne déclenche pas automatiquement `end_session()`
2. **Ctrl+C ne fonctionne pas** - La commande `conversation.end_session()` peut bloquer indéfiniment

## Solutions implémentées

### 1. Signal Handler amélioré (Ctrl+C)

```python
def signal_handler(sig, frame):
    print("\n\nEnding conversation...")
    shutdown_flag.set()

    # Force end with timeout
    def force_end():
        try:
            conversation.end_session()
        except Exception as e:
            print(f"Error ending session: {e}")

    end_thread = threading.Thread(target=force_end)
    end_thread.daemon = True
    end_thread.start()
    end_thread.join(timeout=2.0)  # Max 2 secondes

    save_transcript_on_exit()
    os._exit(0)  # Force exit
```

**Avantages :**
- Timeout de 2 secondes max pour `end_session()`
- Utilise `os._exit(0)` pour forcer la sortie
- Thread daemon pour ne pas bloquer le processus

### 2. Détection de fin de conversation par mots-clés

```python
def on_agent_response(response):
    capture_message("agent", response)
    end_keywords = ["au revoir", "goodbye", "je vais raccrocher", "merci de votre temps", "bonne journée"]
    if any(keyword in response.lower() for keyword in end_keywords):
        print("\n[INFO] Agent is ending the conversation...")
```

**Avantages :**
- Détecte quand l'agent signale la fin de conversation
- Peut être étendu avec plus de mots-clés

### 3. Wait avec monitoring

```python
def wait_with_timeout():
    nonlocal conversation_id
    try:
        conversation_id = conversation.wait_for_session_end()
    except Exception as e:
        print(f"\n[ERROR] Session ended with error: {e}")

wait_thread = threading.Thread(target=wait_with_timeout)
wait_thread.start()
wait_thread.join()
```

**Avantages :**
- Thread séparé pour `wait_for_session_end()`
- Permet l'interruption par Ctrl+C
- Gère les erreurs gracieusement

## Configuration du workflow ElevenLabs

Pour que l'agent termine correctement la conversation, votre noeud "Fin" devrait :

1. **Envoyer un message de clôture** avec un des mots-clés détectés :
   - "Au revoir et merci de votre temps"
   - "Je vais raccrocher. Bonne journée !"
   - "Goodbye, thank you for your time"

2. **Utiliser l'action "End Conversation"** après le message de clôture

## Workflow recommandé

```
Démarrer
  ↓
New subagent (Get information)
  ↓
LLM Condition (détecte fin de conversation)
  ↓
[Si oui] → Action: Envoyer message "Au revoir et merci de votre temps. Je vais raccrocher maintenant."
  ↓
Action: End Conversation
  ↓
Fin
```

## Utilisation

```bash
# Lancer l'agent
python elevenlabsagent.py

# Terminer manuellement
Ctrl+C (fonctionne maintenant correctement avec timeout de 2s)
```

## Améliorations futures possibles

1. **Ajouter un timeout global** pour les conversations très longues
2. **Enrichir les mots-clés de détection** selon vos besoins
3. **Ajouter un callback `callback_session_ended`** si disponible dans le SDK ElevenLabs
4. **Logger les événements** pour déboguer les problèmes de fin de session

## Debugging

Si la conversation ne se termine toujours pas :

1. Vérifiez les logs pour voir si les mots-clés sont détectés
2. Ajoutez des prints dans `on_agent_response()` pour voir tous les messages
3. Vérifiez que votre workflow a bien une action "End Conversation"
4. Utilisez Ctrl+C qui force maintenant la sortie après 2 secondes
