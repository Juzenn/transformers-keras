import numpy as np
import tensorflow as tf

from .modeling_albert import (
    Albert,
    AlbertEmbedding,
    AlbertEncoder,
    AlbertEncoderGroup,
    AlbertEncoderLayer,
    AlbertForPretrainingModel,
    AlbertMLMHead,
    AlbertModel,
    AlbertSOPHead,
)


class ModelingAlbertTest(tf.test.TestCase):

    def testAlbertEmbedding(self):
        embedding = AlbertEmbedding(vocab_size=100, embedding_size=128)
        inputs = (
            tf.constant([[0, 2, 3, 4, 5, 1]]),  # input_ids
            tf.constant([[0, 0, 0, 1, 1, 1]]),  # token_type_ids
        )
        outputs = embedding(inputs, training=True)
        self.assertAllEqual([1, 6, 128], outputs.shape)

    def testAlbertEncoderLayer(self):
        encoder = AlbertEncoderLayer()
        hidden_states = tf.random.uniform(shape=(2, 16, 768))  # hidden states
        mask = tf.constant([[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
                            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1]],
                           shape=(2, 16), dtype=tf.float32)  # mask
        outputs, attn_weights = encoder(inputs=(hidden_states, mask[:, tf.newaxis, tf.newaxis, :]))
        self.assertAllEqual([2, 16, 768], outputs.shape)
        self.assertAllEqual([2, 8, 16, 16], attn_weights.shape)

    def testAlbertEncoderGroup(self):

        hidden_states = tf.random.uniform(shape=(2, 16, 768))  # hidden states
        mask = tf.constant([[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
                            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1]],
                           shape=(2, 16), dtype=tf.float32)  # mask
        mask = mask[:, tf.newaxis, tf.newaxis, :]

        def _run_albert_encoder_group(num_layers_each_group):
            group = AlbertEncoderGroup(num_layers_each_group=num_layers_each_group)
            outputs, group_states, group_attn_weights = group(inputs=(hidden_states, mask))
            self.assertAllEqual([2, 16, 768], outputs.shape)

            self.assertEqual(num_layers_each_group, len(group_states))
            for state in group_states:
                self.assertAllEqual([2, 16, 768], state.shape)

            self.assertEqual(num_layers_each_group, len(group_attn_weights))
            for attention in group_attn_weights:
                self.assertAllEqual([2, 8, 16, 16], attention.shape)

        for layer in [1, 2, 3, 4]:
            _run_albert_encoder_group(layer)

    def testAlbertEncoder(self):
        hidden_states = tf.random.uniform(shape=(2, 16, 768))  # hidden states
        mask = tf.constant([[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
                            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1]],
                           shape=(2, 16), dtype=tf.float32)  # mask
        mask = mask[:, tf.newaxis, tf.newaxis, :]

        encoder = AlbertEncoder(num_layers=4, num_groups=1, num_layers_each_group=1, hidden_size=768)

        outputs, all_states, all_attn_weights = encoder(inputs=(hidden_states, mask))
        self.assertAllEqual([2, 16, 768], outputs.shape)

        self.assertEqual(4, len(all_states))
        for state in all_states:
            self.assertAllEqual([2, 16, 768], state.shape)

        self.assertEqual(4, len(all_attn_weights))
        for attention in all_attn_weights:
            self.assertAllEqual([2, 8, 16, 16], attention.shape)

    def testAlbert(self):
        input_ids = tf.constant(
            [1, 2, 3, 4, 5, 6, 7, 5, 3, 2, 3, 4, 1, 2, 3, 1, 2, 3, 4, 5, 6, 6, 6, 7, 7, 8, 0, 0, 0, 0, 0, 0],
            shape=(2, 16),
            dtype=np.int32)  # input_ids
        token_type_ids = np.array(
            [[0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1],
             [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1]], dtype=np.int64)  # token_type_ids,
        input_mask = tf.constant(
            [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1],
             [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1]], dtype=np.float32)  # input_mask

        model = Albert(vocab_size=100, hidden_size=768,
                       num_layers=4, num_groups=1, num_layers_each_group=1)
        outputs, pooled_outputs, all_states, all_attn_weights = model(inputs=(input_ids, token_type_ids, input_mask))
        self.assertAllEqual([2, 16, 768], outputs.shape)
        self.assertAllEqual([2, 768], pooled_outputs.shape)

        self.assertEqual(4, len(all_states))
        for state in all_states:
            self.assertAllEqual([2, 16, 768], state.shape)

        self.assertEqual(4, len(all_attn_weights))
        for attention in all_attn_weights:
            self.assertAllEqual([2, 8, 16, 16], attention.shape)

    def testAlbertMLMHead(self):
        embedding = AlbertEmbedding(vocab_size=100)
        mlm = AlbertMLMHead(vocab_size=100, embedding=embedding)
        inputs = tf.random.uniform(shape=(2, 16, 768))
        outputs = mlm(inputs)
        self.assertAllEqual([2, 16, 100], outputs.shape)

    def testAlbertSOPHead(self):
        sop = AlbertSOPHead()
        inputs = tf.random.uniform(shape=(2, 768))
        outputs = sop(inputs)
        self.assertAllEqual([2, 2], outputs.shape)

    def testAlberModel(self):
        input_ids = tf.constant(
            [1, 2, 3, 4, 5, 6, 7, 5, 3, 2, 3, 4, 1, 2, 3, 1, 2, 3, 4, 5, 6, 6, 6, 7, 7, 8, 0, 0, 0, 0, 0, 0],
            shape=(2, 16),
            dtype=np.int32)  # input_ids
        token_type_ids = np.array(
            [[0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1],
             [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1]], dtype=np.int64)  # token_type_ids,
        input_mask = tf.constant(
            [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1],
             [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1]], dtype=np.float32)  # input_mask

        model = AlbertModel(vocab_size=100, hidden_size=768,
                            num_layers=4, num_groups=1, num_layers_each_group=1)
        outputs, pooled_outputs = model(inputs=(input_ids, token_type_ids, input_mask))
        self.assertAllEqual([2, 16, 768], outputs.shape)
        self.assertAllEqual([2, 768], pooled_outputs.shape)

    def testAlbertForPretrainingModel(self):
        input_ids = tf.constant(
            [1, 2, 3, 4, 5, 6, 7, 5, 3, 2, 3, 4, 1, 2, 3, 1, 2, 3, 4, 5, 6, 6, 6, 7, 7, 8, 0, 0, 0, 0, 0, 0],
            shape=(2, 16),
            dtype=np.int32)  # input_ids
        token_type_ids = np.array(
            [[0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1],
             [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1]], dtype=np.int64)  # token_type_ids,
        input_mask = tf.constant(
            [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1],
             [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1]], dtype=np.float32)  # input_mask

        model = AlbertForPretrainingModel(vocab_size=100, num_layers=4, num_groups=1, num_layers_each_group=1)
        outputs, pooled_outputs = model(inputs=(input_ids, token_type_ids, input_mask))
        self.assertAllEqual([2, 16, 100], outputs.shape)
        self.assertAllEqual([2, 2], pooled_outputs.shape)


if __name__ == "__main__":
    tf.test.main()
