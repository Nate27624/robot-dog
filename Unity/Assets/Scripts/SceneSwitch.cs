using UnityEngine;

public class SceneSwitch : MonoBehaviour
{
    bool dogOrSettings = false;
    public GameObject[] dog;
    public GameObject[] settings;

    public void MenuPress()
    {
        dogOrSettings = !dogOrSettings;

        if (dogOrSettings)
        {
            for (int i = 0; i < settings.Length; i++)
            {
                settings[i].SetActive(false);
            }

            for (int i = 0; i < dog.Length; i++)
            {
                dog[i].SetActive(true);
            }
        }

        if (!dogOrSettings)
        {
            for (int i = 0; i < settings.Length; i++)
            {
                settings[i].SetActive(true);
            }

            for (int i = 0; i < dog.Length; i++)
            {
                dog[i].SetActive(false);
            }
        }
    }
}
