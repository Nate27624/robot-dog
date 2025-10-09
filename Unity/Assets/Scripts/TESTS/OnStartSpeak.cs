using UnityEngine;

public class OnStartSpeak : MonoBehaviour
{
    public string speak;
    public SpeechOutput spOut;
    public bool speakAgain;
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        spOut.Speak(speak);
    }

    // Update is called once per frame
    void Update()
    {
        // Used for testing the different voices, likely can be deleted later but not important
        if (speakAgain)
        {
            spOut.Speak(speak);
            speakAgain = false;
        }
    }
}
