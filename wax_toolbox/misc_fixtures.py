import betamax
import pandas as pd
import requests


def sanitize_token(interaction, current_cassette):
    """Betamax token sanitizer."""
    headers = interaction.data["request"]["headers"]

    def sanitize_header(name):
        token = headers.get(name)

        # If there was no token header in the response, exit
        if token is not None:
            # Otherwise, create a new placeholder so that when cassette is saved,
            # Betamax will replace the token with our placeholder.
            current_cassette.placeholders.append(
                betamax.cassette.cassette.Placeholder(
                    placeholder="<" + name + ">", replace=token[0]
                )
            )

    sanitize_header("Authorization")


class RecorderBase:
    """
    Context manager that will either record or replay requests call.
    It also proposes a send_object that will either save a DataFrame
    or compare with the saved DataFrame.

    Classic use::

        with record("name-of-my-bucket") as r:
            df = a_function_that_uses_requests(...)
            r.send_dataframe(df)

    """

    def __init__(
        self, bucket_name, sample_dir, session=requests.Session(), betamax_mode="none"
    ):
        self.sample_dir = sample_dir
        self.bucket_name = bucket_name
        self.betamax_mode = betamax_mode
        self.recorder = betamax.Betamax(session)

    def __enter__(self):
        self.rec = self.recorder.use_cassette(
            self.bucket_name, record=self.betamax_mode
        )
        self.rec.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.rec.stop()

    def send_dataframe(self, df):
        if not isinstance(df, pd.DataFrame):
            raise NotImplementedError("Recorder Only works for pandas.DataFrame.")

        if df.empty:
            raise ValueError("DataFrame is empty")

        pickle_path = self.samples_dir / "{}.pickle".format(self.bucket_name)
        csv_path = self.samples_dir / "{}.csv".format(self.bucket_name)

        def dump(df):
            df.to_pickle(pickle_path)
            df.to_csv(csv_path)

        def compare(df):
            df_original = pd.read_pickle(pickle_path)
            pd.testing.assert_frame_equal(df, df_original)

        if self.betamax_mode == "all":
            dump(df)
        elif self.betamax_mode == "once":
            if not pickle_path.exists():
                dump(df)
        elif self.betamax_mode == "none":
            compare(df)
