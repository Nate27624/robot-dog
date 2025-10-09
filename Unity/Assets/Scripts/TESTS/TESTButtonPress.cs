using UnityEngine;
using TMPro;

public class TESTButtonPress : MonoBehaviour
{
    public TMP_Text text;
    bool flip = false;
    public AudioSource sauce;
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        
    }

    // Update is called once per frame
    void Update()
    {
        
    }

    public void OnClickChangeText()
    {
        flip = !flip;

        if (flip)
        {
            text.text = "Cat";
        }
        else
        {
            text.text = "Dog";
        }

        sauce.Play();
    }
}
