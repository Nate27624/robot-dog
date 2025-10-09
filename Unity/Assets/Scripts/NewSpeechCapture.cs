using Meta.WitAi;
using Meta.WitAi.Dictation;
using Meta.WitAi.Requests;
using Meta.WitAi.Configuration;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Analytics;
//using Meta.Voice.Samples.Dictation;
using Meta.WitAi.Events;
using System.Text;
using System;
using TMPro;

public class NewSpeechCapture : MonoBehaviour
{
    public AudioSource audioSource;
    [SerializeField] private DictationService witDictation;
    public string _activeText;
    public TMP_Text tmpText;
    public NgrokConnection ngrok;

    public bool enableMic = true;
    public bool micWasEnabled = false;
    public Color userSpeakingColor;
    private void Awake()
    {
        if (!witDictation) witDictation = FindObjectOfType<DictationService>();
    }

    public void Update()
    {
        if (enableMic)
        {
            // Activate mic if it's not already active and allowed
            if (!witDictation.MicActive && witDictation.CanActivateAudio())
            {
                witDictation.ActivateImmediately();
            }
        }
        else
        {
            // Deactivate if it's still active
            if (witDictation.MicActive)
            {
                witDictation.Deactivate();
            }
        }

        Debug.Log("Mirophone Status: " + witDictation.MicActive);
    }

    private void OnEnable()
    {
        witDictation.DictationEvents.OnFullTranscription.AddListener(OnFullTranscription);
        witDictation.DictationEvents.OnError.AddListener(OnError);
        witDictation.DictationEvents.OnPartialTranscription.AddListener(OnPartialTrans);
    }

    private void OnDisable()
    {
        _activeText = string.Empty;
        witDictation.DictationEvents.OnFullTranscription.RemoveListener(OnFullTranscription);
        witDictation.DictationEvents.OnError.RemoveListener(OnError);
    }

    private void OnFullTranscription(string text)
    {
        if(text == "")
        {
            return;
        }

        Debug.Log("Spoken text >> " + text);
        tmpText.text = text;

        // Send the data to the server
        ngrok.SendQuestion(text);

        _activeText = string.Empty;
        audioSource.Play();
    }

    private void OnPartialTrans(string text)
    {
        if(text == "")
        {
            return;
        }

        tmpText.color = userSpeakingColor;
        tmpText.text = text;
    }

    private void OnError(string error, string er)
    {
        Debug.Log(error);
        Debug.Log(er);
    }
}
