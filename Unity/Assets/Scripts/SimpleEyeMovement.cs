using UnityEngine;
using System.Collections;

public class SimpleEyeMovement : MonoBehaviour
{
    public GameObject irisL;
    public GameObject irisR;

    public GameObject pupilL;
    public GameObject pupilR;

    public GameObject eyeLid;

    public float blinkTimer = 1.00f;

    private float blinkDuration = 0.05f;
    private float blinkDistance = 3.25f;

    public float eyeMoveRadius = 0.1f; // max movement in local space
    public float lookSpeed = 5f;       // higher = faster eye movement
    private Vector3 irisLOriginalPos;
    private Vector3 irisROriginalPos;


    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        if (irisL != null) irisLOriginalPos = irisL.transform.localPosition;
        if (irisR != null) irisROriginalPos = irisR.transform.localPosition;

        StartPupilDilation();
        StartCoroutine(RandomEyeMovement());
    }

    // Update is called once per frame
    void Update()
    {
        if(blinkTimer > 0)
        {
            blinkTimer -= Time.deltaTime;
        }
        else
        {
            Blink();
            blinkTimer = RandomNormal(3.5f, 1.0f);
        }
    }

    float RandomNormal(float mean = 0f, float stdDev = 1f)
    {
        float u1 = 1.0f - Random.value; // Uniform(0,1] random doubles
        float u2 = 1.0f - Random.value;
        float randStdNormal = Mathf.Sqrt(-2.0f * Mathf.Log(u1)) *
                              Mathf.Sin(2.0f * Mathf.PI * u2); // Random normal (mean 0, stddev 1)
        return mean + stdDev * randStdNormal; // Scale and shift
    }

    IEnumerator BlinkRoutine()
    {
        Vector3 originalPos = eyeLid.transform.localPosition;

        // Add slight random variation to distance and duration
        float offset = RandomNormal(0f, 0.02f); // distance variation
        float timeOffset = Mathf.Clamp(RandomNormal(0f, 0.01f), -0.02f, 0.02f); // duration variation

        float moveDistance = blinkDistance + offset;
        float moveTime = Mathf.Max(0.01f, blinkDuration + timeOffset); // ensure positive time

        Vector3 downPos = originalPos + Vector3.down * moveDistance;

        // Move down
        yield return MoveOverTime(eyeLid, originalPos, downPos, moveTime);

        // Move up
        yield return MoveOverTime(eyeLid, downPos, originalPos, moveTime);
    }

    IEnumerator MoveOverTime(GameObject target, Vector3 start, Vector3 end, float duration)
    {
        float elapsed = 0f;
        while (elapsed < duration)
        {
            target.transform.localPosition = Vector3.Lerp(start, end, elapsed / duration);
            elapsed += Time.deltaTime;
            yield return null;
        }
        target.transform.localPosition = end;
    }

    public void Look(Vector2 direction)
    {
        float maxOffset = 0.1f; // max movement from center (in local space)

        // Add slight jitter to make the motion feel alive
        float jitterX = RandomNormal(0f, 0.005f);
        float jitterY = RandomNormal(0f, 0.005f);
        Vector2 jitteredDir = direction.normalized + new Vector2(jitterX, jitterY);
        Vector2 clampedDir = Vector2.ClampMagnitude(jitteredDir, 1f);

        Vector3 irisOffset = new Vector3(clampedDir.x, clampedDir.y, 0f) * maxOffset;

        if (irisL != null) irisL.transform.localPosition = irisOffset;
        if (irisR != null) irisR.transform.localPosition = irisOffset;
    }

    public void StartPupilDilation()
    {
        StartCoroutine(DilationRoutine());
    }
    IEnumerator DilationRoutine()
    {
        float baseScale = 0.35f;
        float scaleVariation = 0.03f;

        float currentScale = baseScale;
        float targetScale = baseScale;

        while (true)
        {
            // Pick a new target scale less frequently
            targetScale = Mathf.Clamp(
                baseScale + RandomNormal(0f, scaleVariation * 0.3f),
                baseScale - scaleVariation,
                baseScale + scaleVariation);

            float elapsed = 0f;
            float duration = Random.Range(1.5f, 3f); // slower changes (1.5 to 3 seconds)

            while (elapsed < duration)
            {
                elapsed += Time.deltaTime;
                currentScale = Mathf.Lerp(currentScale, targetScale, elapsed / duration);

                Vector3 newScale = Vector3.one * currentScale;
                if (pupilL != null) pupilL.transform.localScale = newScale;
                if (pupilR != null) pupilR.transform.localScale = newScale;

                yield return null;
            }
        }
    }


    IEnumerator RandomEyeMovement()
    {
        Vector2 currentDir = Vector2.zero;

        while (true)
        {
            // New (uses random direction with variable magnitude)
            float angle = Random.Range(0f, Mathf.PI * 2f);
            float strength = Mathf.Clamp01(Mathf.Abs(RandomNormal(0.2f, 0.3f))); // Mostly small moves

            Vector2 targetDir = new Vector2(Mathf.Cos(angle), Mathf.Sin(angle)) * strength;


            float t = 0f;
            float duration = Random.Range(0.2f, 0.6f); // how long the eye takes to saccade

            // Smoothly move from currentDir to targetDir
            while (t < 1f)
            {
                t += Time.deltaTime * lookSpeed;
                Vector2 smoothDir = Vector2.Lerp(currentDir, targetDir, Mathf.SmoothStep(0f, 1f, t));
                MoveIris(smoothDir);
                yield return null;
            }

            currentDir = targetDir;

            // Hold gaze for a random time (normal distribution)
            float holdTime = Mathf.Clamp(RandomNormal(0.5f, 0.3f), 0.1f, 1.2f);
            yield return new WaitForSeconds(holdTime);
        }
    }

    void MoveIris(Vector2 direction)
    {
        Vector2 offset = direction * eyeMoveRadius;
        Vector3 offset3 = new Vector3(offset.x, offset.y, 0f);

        if (irisL != null) irisL.transform.localPosition = irisLOriginalPos + offset3;
        if (irisR != null) irisR.transform.localPosition = irisROriginalPos + offset3;
    }





    public void Blink()
    {
        if (eyeLid != null)
            StartCoroutine(BlinkRoutine());
        else
            Debug.LogWarning("eyeLid GameObject is not assigned.");
    }

}
