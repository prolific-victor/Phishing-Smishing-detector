# Real training data

`fetch_real_datasets.py` downloads the following public datasets and writes normalized CSVs. It parses the records locally; it does not visit the URLs in the URL corpus.

## URL model

- Source: [PhiUSIIL Phishing URL (Website) Dataset](https://archive.ics.uci.edu/dataset/967/phiusiil%2Bphishing%2Burl%2Bwebsite), Arvind Prasad and Shalini Chandra, 2024.
- DOI: <https://doi.org/10.1016/j.cose.2023.103545>
- License: CC BY 4.0.
- Preparation: keep only raw `URL` and `label`; convert UCI's `0 = phishing, 1 = legitimate` into this project's `1 = phishing, 0 = legitimate`; remove duplicate URLs and conflicting labels.

## Message model

- Source: [SMS Phishing Dataset for Machine Learning and Pattern Recognition](https://data.mendeley.com/datasets/f45bkkt8pr/1), Sandhya Mishra and Devpriya Soni, 2022.
- DOI: <https://doi.org/10.17632/f45bkkt8pr.1>
- License: CC BY 4.0.
- Preparation: use the message text; map `smishing` to `1` and both `ham` and generic `spam` to `0`; remove duplicate messages and conflicting labels. Ham means ordinary non-phishing messages. Generic spam means unsolicited junk; it is not automatically phishing, so it belongs in the negative class for this phishing-specific detector.

The message corpus is older and imbalanced. Validation scores are a benchmark on these source datasets, not a guarantee about current attacks or any individual link/message. URL scans can use an optional Google Safe Browsing v5 live reputation check when `GOOGLE_SAFE_BROWSING_API_KEY` is configured; an unlisted URL is not necessarily safe. The submitted URL is sent to Google for lookup.
