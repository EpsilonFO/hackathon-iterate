# 🎤 Guide de Configuration pour Démo Live (Sans Écouteurs)

## Problème Résolu
✅ Suppression du feedback audio (écho) quand l'agent s'entend lui-même via le haut-parleur

## Comment ça Marche

L'interface audio personnalisée (`EchoCancellationAudioInterface`) :
1. **Détecte quand l'agent parle** et ignore le microphone pendant ce temps
2. **Attend un délai** après que l'agent termine (0.8 secondes par défaut)
3. **Calibre automatiquement** le bruit ambiant au démarrage
4. **Utilise un seuil de volume adaptatif** pour détecter seulement votre voix

## Installation

Aucune dépendance supplémentaire requise ! Le code utilise seulement PyAudio qui est déjà installé.

## Utilisation

### Option 1 : Mode Démo (Avec Suppression d'Écho) - RECOMMANDÉ
```bash
cd elevenlabsdemo
source .venv/bin/activate
python elevenlabsagent.py
```

Par défaut, la suppression d'écho est **activée**.

### Option 2 : Mode Standard (Avec Écouteurs)
Si vous voulez utiliser l'interface par défaut avec des écouteurs :

Modifiez le fichier `.env` ou le code pour désactiver l'écho cancellation.

## Configuration Optimale pour la Démo

### 1. **Positionnement du Matériel**
- 🎤 **Microphone** : Placez-le proche de vous (15-30 cm)
- 🔊 **Haut-parleur** : Éloignez-le du micro (au moins 50 cm)
- 📐 **Angle** : Orientez le micro vers vous, pas vers le haut-parleur

### 2. **Réglages Audio**
- 🔉 **Volume du haut-parleur** : 50-70% (pas trop fort)
- 🎚️ **Volume du micro** : Niveau moyen (70-80%)
- 🔇 **Environnement** : Limitez le bruit ambiant autant que possible

### 3. **Calibration Automatique**
Au lancement, le système calibre pendant 2 secondes :
```
🔇 Calibrating noise floor (please stay quiet for 2 seconds)...
✅ Calibration complete. Noise floor: 0.0234
```

**⚠️ IMPORTANT** : Restez silencieux pendant la calibration !

## Ajustements Fins

Si vous avez encore des problèmes de feedback, ajustez ces paramètres dans [`elevenlabsagent.py`](elevenlabsagent.py#L100-L103) :

```python
audio_interface = EchoCancellationAudioInterface(
    volume_threshold=0.02,    # ⬆️ Augmentez (0.03-0.05) si trop sensible
                              # ⬇️ Diminuez (0.01-0.015) si pas assez sensible
    silence_duration=0.8      # ⬆️ Augmentez (1.0-1.5) si l'agent se coupe
                              # ⬇️ Diminuez (0.5-0.7) pour réponse plus rapide
)
```

## Indicateurs Visuels

Pendant la conversation, vous verrez :
- `[AGENT]: ...` - L'agent parle (micro ignoré)
- `[USER]: ...` - Votre message détecté
- `🎤 Listening for your response...` - Le micro est réactivé après que l'agent termine

## Dépannage

### Problème : L'agent m'entend quand il parle
**Solution** : Augmentez `silence_duration` à 1.0 ou plus

### Problème : Le système ne détecte pas ma voix
**Solution** :
- Baissez `volume_threshold` à 0.015
- Parlez plus fort ou rapprochez le micro
- Refaites la calibration (relancez le programme)

### Problème : Trop de bruit ambiant capturé
**Solution** :
- Augmentez `volume_threshold` à 0.03
- Fermez les fenêtres / désactivez la ventilation
- Utilisez un micro directionnel

### Problème : Latence dans la réponse
**Solution** : Diminuez `silence_duration` à 0.5

## Test Rapide

Pour tester l'interface audio seule :
```bash
python echo_cancellation_audio.py
```

Cela affichera la liste des périphériques audio disponibles.

## Recommandations pour une Démo Parfaite

1. ✅ **Testez avant la démo** dans la même salle avec le même matériel
2. ✅ **Calibrez à chaque lancement** (restez silencieux 2 secondes)
3. ✅ **Parlez clairement** avec des pauses entre vos phrases
4. ✅ **Attendez l'indicateur** 🎤 avant de parler
5. ✅ **Évitez de parler en même temps** que l'agent

## Matériel Recommandé (Optionnel)

Pour une démo optimale :
- 🎤 **Micro USB directionnel** (ex: Blue Yeti, Rode NT-USB)
- 🔊 **Haut-parleur Bluetooth** éloigné du micro
- 🎧 **Plan B** : Gardez des écouteurs à portée de main !

---

**Astuce Pro** 💡 : Pour une démo live devant un public, utilisez un micro-cravate (lavalier) et des enceintes de salle. Le micro sera près de votre bouche et loin des enceintes.
