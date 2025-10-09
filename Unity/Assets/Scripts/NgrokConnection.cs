using UnityEngine;
using UnityEngine.Networking;
using System.Collections;
using TMPro; // Optional: if you're using a TextMeshPro input/output
using UnityEngine.UI;

public class NgrokConnection : MonoBehaviour
{
    public TMP_InputField addressInput;
    public TMP_Text resultText;
    public TMP_Text speakText;
    public Button btn;

    public Color successColor;
    public Color robotDogColor;
    public SceneSwitch ss;
    public SpeechOutput speech;

    public void TestConnection()
    {
        StartCoroutine(SendTestRequest());
    }

    public void SendQuestion(string question)
    {
        Debug.Log("Sending Question...");
        StartCoroutine(SendQuestionRequest(question));
        
    }

    private IEnumerator SendQuestionRequest(string question)
    {
        // Create JSON payload
        string jsonPayload = JsonUtility.ToJson(new QuestionData(question));
        byte[] jsonToSend = new System.Text.UTF8Encoding().GetBytes(jsonPayload);

        // Create the UnityWebRequest
        UnityWebRequest request = new UnityWebRequest("https://" + addressInput.text + ".ngrok-free.app/ask_question", "POST");
        request.uploadHandler = new UploadHandlerRaw(jsonToSend);
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/json");

        // Send the request
        yield return request.SendWebRequest();

        Debug.Log("HERE");

        if (request.result == UnityWebRequest.Result.Success)
        {
            Debug.Log("Raw Response: " + request.downloadHandler.text);

            QuestionResponse res = JsonUtility.FromJson<QuestionResponse>(request.downloadHandler.text);
            Debug.Log("Parsed Response: " + res.response);

            ProcessResponse(res.response);
        }

        else
        {
            Debug.LogError("Error: " + request.error);
            Debug.LogError("Response code: " + request.responseCode);
            Debug.LogError("Response text: " + request.downloadHandler.text);
        }
    }


    private IEnumerator SendTestRequest()
    {
        UnityWebRequest request = UnityWebRequest.Get("https://" + addressInput.text + ".ngrok-free.app/test_connection");

        // Send request
        yield return request.SendWebRequest();

        // Handle result
        if (request.result == UnityWebRequest.Result.Success)
        {
            Debug.Log("Backend is reachable: " + request.downloadHandler.text);
            if (resultText != null)
            {
                resultText.text = "Connected!";
                ColorBlock colors = btn.colors;
                colors.normalColor = successColor;
                btn.colors = colors;

                ss.MenuPress();
            }
        }
        else
        {
            Debug.LogError("Connection failed: " + request.error);
            if (resultText != null)
                resultText.text = "Error: " + request.error;
        }
    }

    // Helper class for JSON serialization
    [System.Serializable]
    public class QuestionData
    {
        public string user_question;

        public QuestionData(string question)
        {
            user_question = question;
        }
    }

    [System.Serializable]
    public class QuestionResponse
    {
        public string response;
    }


    public void ProcessResponse(string response)
    {
        speech.Speak(response);
        speakText.text = response;
        speakText.color = robotDogColor;
    }
}
